from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm.session import Session

from app.db.crud import ConfigRepository
from app.db.database import get_db
from app.db.models import ServiceConfig
from app.schemas.config_schema import ConfigResponse, ConfigUpdateSchema
from app.core.security import verify_api_key

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


@router.get("/list", dependencies=[Depends(verify_api_key)])
def list_configs(db: Session = Depends(get_db)):
    """
    List all available service configurations.
    Requires API key authentication.
    """
    # Query the ServiceConfig model directly and return serializable data
    configs = db.query(ServiceConfig).all()

    result = []
    for c in configs:
        result.append({
            "id": c.id,
            "name": c.name,
            "config": c.config,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        })

    return {"configs": result}

@router.get("/get", response_model=ConfigResponse, dependencies=[Depends(verify_api_key)])
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
    updated = repo.update_or_create_config(data=data)
    return updated


@router.get("/versions/{service_name}", dependencies=[Depends(verify_api_key)])
def list_versions(service_name: str, db: Session = Depends(get_db)):
    """
    List all configuration versions for a given service.
    Requires API key authentication.
    """
    repo = ConfigRepository(db)
    versions = repo.list_versions(service_name)
    return {"service_name": service_name, "versions": versions}