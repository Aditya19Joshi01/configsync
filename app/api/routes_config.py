from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm.session import Session

from app.db.crud import ConfigRepository
from app.db.database import get_db
from app.db.models import User
from app.schemas.config_schema import ConfigResponse, ConfigUpdateSchema
from app.core.security import get_current_user

router = APIRouter(prefix="/config", tags=["Configuration"])

@router.get("/health")
def health_check():
    """
    Health check endpoint to verify the service is running.
    Example: GET /config/health
    """
    db = next(get_db())
    # Simple DB operation to ensure connectivity
    return {"api_status": "ok", "db_status": "connected" if db else "disconnected"}


@router.get("/list", dependencies=[Depends(get_current_user)])
def list_configs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    List all available service configurations for the current user.
    Requires authentication.
    """
    repo = ConfigRepository(db)
    configs = repo.list_all_configs_for_user(user.id)

    result = []
    for c in configs:
        result.append({
            "id": c.id,
            "name": c.name,
            "config": c.config,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        })

    return {"configs": result}

@router.get("/get", response_model=ConfigResponse, dependencies=[Depends(get_current_user)])
def get_config(service: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Fetch the configuration for a given service for the current user.
    Example: GET /config/get?service=payment-service
    """
    repo = ConfigRepository(db)
    config = repo.get_config(service, user.id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service config not found"
        )

    return config


@router.post("/update", response_model=ConfigResponse, dependencies=[Depends(get_current_user)])
def update_config(data: ConfigUpdateSchema, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Update or insert a configuration for a service for the current user.
    Requires authentication.
    """
    repo = ConfigRepository(db)
    updated = repo.update_or_create_config(data=data, user_id=user.id)
    return updated


@router.get("/versions/{service_name}", dependencies=[Depends(get_current_user)])
def list_versions(service_name: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    List all configuration versions for a given service for the current user.
    Requires authentication.
    """
    repo = ConfigRepository(db)
    versions = repo.list_versions(service_name, user.id)
    return {"service_name": service_name, "versions": versions}