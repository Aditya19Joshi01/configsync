from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm.session import Session
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Security

from app.core.security import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, decode_access_token, oauth2_scheme
from app.db.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.db.models import User, RevokedToken
from app.tasks.logger import (
    user_login_log, user_logout_log, user_registration_log,
    user_login_log_sync, user_logout_log_sync, user_registration_log_sync
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter_by(username=user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_pw = get_password_hash(user.password)
    # default role handled by DB default if not provided
    new_user = User(username=user.username, email=user.email, role=user.role, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    try:
        user_registration_log.delay(user_email=new_user.email, user_role=new_user.role)
    except Exception as e:
        # Broker might be unavailable; fallback to sync logging
        print(f"[auth] failed to enqueue user_registration_log: {e}")
        user_registration_log_sync(new_user.email, new_user.role)
    return new_user

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm gives .username and .password from form data
    db_user = db.query(User).filter_by(username=form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token, jti, expires = create_access_token(
        data={"sub": db_user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    try:
        user_login_log.delay(user_email=db_user.email)
    except Exception as e:
        print(f"[auth] failed to enqueue user_login_log: {e}")
        user_login_log_sync(db_user.email)
    return {"access_token": token, "token_type": "bearer", "jti": jti, "expires_at": expires.isoformat()}

@router.post("/logout")
def logout(token: str = Security(oauth2_scheme), db: Session = Depends(get_db)):
    # Decode to extract jti and subject
    payload = decode_access_token(token)
    jti = payload.get("jti")
    sub = payload.get("sub")
    if not jti:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No jti in token")

    # find user if possible
    user = None
    if sub:
        user = db.query(User).filter_by(username=sub).first()

    # store revoked token
    revoked = RevokedToken(jti=jti, user_id=getattr(user, 'id', None), expires_at=None)
    db.add(revoked)
    db.commit()
    try:
        user_logout_log.delay(user_email=getattr(user, 'email', None))
    except Exception as e:
        print(f"[auth] failed to enqueue user_logout_log: {e}")
        user_logout_log_sync(getattr(user, 'email', None))
    return {"msg": "logged out"}
