from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm.session import Session
from typing import Optional

from app.db.crud import ConfigRepository
from app.db.database import get_db
from app.db.models import User
from app.schemas.config_schema import ConfigResponse, ConfigUpdateSchema
from app.core.security import get_current_user
from app.tasks.logger import (
    log_config_update, log_config_retrieval,
    log_config_update_sync, log_config_retrieval_sync, log_config_delete, log_config_version_compare,
    log_config_version_compare_sync, log_config_version_rollback, log_config_version_rollback_sync
)

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
def list_configs(
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
        target_user_id: Optional[int] = Query(None, description="(admin-only) user id to list configs for")
):
    """
    List available service configurations.
    - Admins: can pass `target_user_id` to list another user's configs or omit to list all configs.
    - Normal users: only their own configs (ignore `target_user_id`).
    """
    repo = ConfigRepository(db)

    if getattr(user, 'role', None) != 'admin':
        # ignore any target_user_id and force user's own id
        target_user_id = user.id

    configs = repo.list_all_configs_for_user(user_id=target_user_id, current_user=user)

    result = []
    for c in configs:
        result.append({
            "id": c.id,
            "name": c.name,
            "config": c.config,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            "user_id": c.user_id,
        })
        # Try to enqueue logging; fallback to sync if broker unavailable
        try:
            log_config_retrieval.delay(service_name=c.name, user_email=user.email)
        except Exception as e:
            print(f"[routes_config] failed to enqueue log_config_retrieval: {e}")
            log_config_retrieval_sync(c.name, user.email)

    return {"configs": result}

@router.get("/get", response_model=ConfigResponse, dependencies=[Depends(get_current_user)])
def get_config(
        service: str,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
        target_user_id: Optional[int] = Query(None, description="(admin-only) user id to fetch config for")
):
    """
    Fetch the configuration for a given service.
    - Admins: may specify `target_user_id` or omit to fetch the first matching service across users.
    - Normal users: will only fetch their own service config.
    """
    repo = ConfigRepository(db)

    if getattr(user, 'role', None) != 'admin':
        target_user_id = user.id

    config = repo.get_config(service, user_id=target_user_id, current_user=user)

    # Try to enqueue logging; fallback to sync if broker unavailable
    try:
        log_config_retrieval.delay(service_name=service, user_email=user.email)
    except Exception as e:
        print(f"[routes_config] failed to enqueue log_config_retrieval: {e}")
        log_config_retrieval_sync(service, user.email)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service config not found"
        )

    return config


@router.post("/update", response_model=ConfigResponse, dependencies=[Depends(get_current_user)])
def update_config(
        data: ConfigUpdateSchema,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
        target_user_id: Optional[int] = Query(None, description="(admin-only) user id to update config for")
):
    """
    Update or insert a configuration for a service.
    - Admins: may pass `target_user_id` to update another user's config.
    - Normal users: update their own config only.
    """
    repo = ConfigRepository(db)

    if getattr(user, 'role', None) != 'admin':
        target_user_id = user.id

    updated = repo.update_or_create_config(data=data, user_id=target_user_id, current_user=user)
    try:
        log_config_update.delay(service_name=data.name, user_email=user.email)
    except Exception as e:
        print(f"[routes_config] failed to enqueue log_config_update: {e}")
        log_config_update_sync(data.name, user.email)
    return updated


@router.get("/versions/{service_name}", dependencies=[Depends(get_current_user)])
def list_versions(
        service_name: str,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
        target_user_id: Optional[int] = Query(None, description="(admin-only) user id to list versions for")
):
    """
    List all configuration versions for a given service.
    - Admins: may pass `target_user_id` to list versions for another user or omit to list versions across users for that service name.
    - Normal users: list versions only for their own service.
    """
    repo = ConfigRepository(db)

    if getattr(user, 'role', None) != 'admin':
        target_user_id = user.id

    versions = repo.list_versions(service_name, user_id=target_user_id, current_user=user)
    return {"service_name": service_name, "versions": versions}


@router.post("/rollback/{service_name}", response_model=ConfigResponse, dependencies=[Depends(get_current_user)])
def rollback_config(
        service_name: str,
        target_version_id: int = Query(..., description="ID of the version to roll back to"),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
        target_user_id: Optional[int] = Query(None, description="(admin-only) user id to roll back config for")
):
    """
    Rollback the configuration of a given service to a specified version.
    - Admins: may pass `target_user_id` to roll back another user's config.
    - Normal users: roll back their own config only.
    """
    repo = ConfigRepository(db)

    if getattr(user, 'role', None) != 'admin':
        target_user_id = user.id

    rolled_back = repo.rollback_to_version(
        service_name,
        target_version_id,
        user_id=target_user_id,
    )
    try:
        log_config_version_rollback.delay(
            service_name=service_name,
            user_email=user.email,
            target_version=target_version_id
        )
    except Exception as e:
        print(f"[routes_config] failed to enqueue log_config_version_rollback: {e}")
        log_config_version_rollback_sync(
            service_name,
            user.email,
            target_version_id
        )
    return rolled_back


@router.get("/diff/{service_name}", dependencies=[Depends(get_current_user)])
def diff_versions(
        service_name: str,
        version1_id: int = Query(..., description="ID of the first version to compare"),
        version2_id: int = Query(..., description="ID of the second version to compare"),
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
        target_user_id: Optional[int] = Query(None, description="(admin-only) user id to diff versions for")
):
    """
    Compute the diff between two configuration versions for a given service.
    - Admins: may pass `target_user_id` to diff versions for another user.
    - Normal users: diff versions only for their own service.
    """
    repo = ConfigRepository(db)

    if getattr(user, 'role', None) != 'admin':
        target_user_id = user.id

    diff_result = repo.diff_versions(service_name, version1_id, version2_id, user_id=target_user_id)

    try:
        log_config_version_compare.delay(
            service_name=service_name,
            user_email=user.email,
            version1=version1_id,
            version2=version2_id
        )
    except Exception as e:
        print(f"[routes_config] failed to enqueue log_config_version_compare: {e}")
        log_config_version_compare_sync(
            service_name,
            user.email,
            version1_id,
            version2_id
        )
    return diff_result


@router.delete("/delete/{service_name}", dependencies=[Depends(get_current_user)])
def delete_config(
        service_name: str,
        db: Session = Depends(get_db),
        user: User = Depends(get_current_user),
        target_user_id: Optional[int] = Query(None, description="(admin-only) user id to delete config for")
):
    """
    Delete the configuration for a given service.
    - Admins: may pass `target_user_id` to delete another user's config.
    - Normal users: delete their own config only.
    """
    repo = ConfigRepository(db)

    if getattr(user, 'role', None) != 'admin':
        target_user_id = user.id

    success = repo.delete_config(service_name, user_id=target_user_id, current_user=user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service config not found"
        )
    try:
        log_config_delete.delay(service_name=service_name, user_email=user.email)
    except Exception as e:
        print(f"[routes_config] failed to enqueue log_config_update: {e}")
        log_config_update_sync(service_name, user.email)
    return {"detail": "Service config deleted successfully"}