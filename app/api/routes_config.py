from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm.session import Session

from app.db.crud import ConfigRepository
from app.db.database import get_db
from app.schemas.config_schema import ConfigResponse, ConfigUpdateSchema
from app.core.security import verify_api_key

router = APIRouter(prefix="/config", tags=["Configuration"])

@router.get("/get", response_model=ConfigResponse)
def get_config(service: str, db: Session = Depends(get_db)):
    """
    Fetch the configuration for a given service.
    Example: GET /config/get?service=payment-service
    """
    repo = ConfigRepository(db)
    config = repo.get_config(service)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service config not found"
        )

    return config


@router.post("/update", response_model=ConfigResponse, dependencies=[Depends(verify_api_key)])
def update_config(data: ConfigUpdateSchema, db: Session = Depends(get_db)):
    """
    Update or insert a configuration for a service.
    Requires API key authentication.
    """
    repo = ConfigRepository(db)
    updated = repo.update_config(data)
    return updated