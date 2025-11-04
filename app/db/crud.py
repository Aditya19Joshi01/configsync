from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from deepdiff import DeepDiff

from app.db.models import ServiceConfig, ConfigVersion, User
from app.schemas.config_schema import ConfigUpdateSchema


class ConfigRepository:
    """
    Handles all database operations related to service configurations.
    Acts as an abstraction layer between the DB and business logic.
    Now supports RBAC: if `current_user` is admin, operations may span all users.
    """

    def __init__(self, db: Session):
        self.db = db

    def _is_admin(
            self,
            current_user: Optional[User]
    ) -> bool:
        return getattr(current_user, 'role', None) == 'admin'

    def get_config(
            self,
            service_name: str,
            user_id: Optional[int] = None,
            current_user: Optional[User] = None
    ):
        """Fetch the configuration for a given service. If current_user is admin and user_id is None, don't filter by user."""
        query = self.db.query(ServiceConfig)
        if self._is_admin(current_user):
            # admin: allow specifying a target user_id or no restriction
            if user_id is not None:
                query = query.filter_by(name=service_name, user_id=user_id)
            else:
                query = query.filter_by(name=service_name)
        else:
            # normal user: require user_id
            if user_id is None:
                raise ValueError("user_id is required for non-admin operations")
            query = query.filter_by(name=service_name, user_id=user_id)

        return query.first()

    def update_or_create_config(
            self,
            data: ConfigUpdateSchema | None = None,
            config_data: ConfigUpdateSchema | None = None,
            user_id: int | None = None,
            current_user: Optional[User] = None
    ):
        """Update existing config or create a new one for the given user.

        Admins may omit user_id to operate globally (or pass a specific user_id).
        Behavior change: if an admin omits user_id and a config with the given name exists for some user,
        update that existing config (preserve its owner) so the owner sees the admin's changes. If no
        existing config exists, create a new config owned by the admin (or by `user_id` if provided).
        """
        input_data = data or config_data
        if input_data is None:
            raise ValueError("No configuration data provided to update_or_create_config")

        # Attempt to find an existing config according to permissions/context
        db_config = self.get_config(input_data.name, user_id=user_id, current_user=current_user)

        if db_config:
            # Update the found config (preserve its user_id)
            db_config.config = input_data.config
            self.db.commit()
            self.db.refresh(db_config)
            owner_id = db_config.user_id
        else:
            # No existing config found. Determine owner for the new config:
            # - If caller provided a user_id, use it.
            # - Else if current_user present, default to current_user.id (admin will own it unless they specified user_id).
            # - For non-admins, user_id must be provided via current_user.
            if user_id is None:
                if current_user is None:
                    raise ValueError("user_id is required to scope config operations")
                owner_id = getattr(current_user, 'id', None)
            else:
                owner_id = user_id

            if owner_id is None:
                raise ValueError("Unable to determine owner for new config")

            db_config = ServiceConfig(name=input_data.name, config=input_data.config, user_id=owner_id)
            self.db.add(db_config)
            self.db.commit()
            self.db.refresh(db_config)

        # Add a version entry for history under the owner of the config (so the owner sees the change)
        self.add_new_version(db_config.name, input_data.config, db_config.user_id)
        return db_config

    def get_latest_version(
            self,
            service_name: str,
            user_id: int,
            current_user: Optional[User] = None
    ):
        """Fetch the latest configuration version for a given service for the user."""
        db = self.db
        query = db.query(ConfigVersion)
        if self._is_admin(current_user):
            if user_id is not None:
                query = query.filter_by(service_name=service_name, user_id=user_id)
            else:
                query = query.filter_by(service_name=service_name)
        else:
            query = query.filter_by(service_name=service_name, user_id=user_id)

        return query.order_by(ConfigVersion.version.desc()).first()

    def add_new_version(
            self,
            service_name: str,
            config: dict,
            user_id: int
    ):
        """Add a new configuration version for a given service for the user."""
        latest_version = self.get_latest_version(service_name, user_id)
        new_version_number = (
            latest_version.version + 1 if latest_version else 1
        )

        new_version = ConfigVersion(
            service_name=service_name,
            version=new_version_number,
            config=config,
            user_id=user_id,
        )
        self.db.add(new_version)
        self.db.commit()
        self.db.refresh(new_version)
        return new_version

    def list_versions(
            self,
            service_name: str,
            user_id: Optional[int] = None,
            current_user: Optional[User] = None
    ):
        """List all configuration versions for a given service for the user.

        Admins may omit user_id to list across all users.
        """
        db = self.db
        print("Attempting to list versions with user_id:", user_id)
        query = db.query(ConfigVersion)
        if self._is_admin(current_user):
            if user_id is not None:
                query = query.filter_by(service_name=service_name, user_id=user_id)
            else:
                query = query.filter_by(service_name=service_name)
        else:
            if user_id is None:
                raise ValueError("user_id is required for non-admin operations")
            query = query.filter_by(service_name=service_name, user_id=user_id)

        print("Constructed query for listing versions:", query)
        return query.order_by(ConfigVersion.version.desc()).all()

    def list_all_configs_for_user(
            self,
            user_id: Optional[int] = None,
            current_user: Optional[User] = None
    ):
        """Helper to list current service configs. If admin and user_id is None, returns all configs."""
        query = self.db.query(ServiceConfig)
        if self._is_admin(current_user):
            if user_id is not None:
                query = query.filter_by(user_id=user_id)
            # else admin: no filter -> return everything
        else:
            if user_id is None:
                raise ValueError("user_id is required for non-admin operations")
            query = query.filter_by(user_id=user_id)

        return query.all()

    def diff_versions(
            self,
            service_name: str,
            version1_id: int,
            version2_id: int,
            user_id: int
    ):
        """Compute the diff between two configuration versions for a given service and user."""
        v1 = self.db.query(ConfigVersion).filter_by(
            service_name=service_name, user_id=user_id, id=version1_id
        ).first()
        v2 = self.db.query(ConfigVersion).filter_by(
            service_name=service_name, user_id=user_id, id=version2_id
        ).first()

        if not v1 or not v2:
            raise HTTPException(status_code=404, detail="One or both versions not found")

        diff = DeepDiff(v1.config, v2.config, ignore_order=True).to_dict()
        return {
            "service": service_name,
            "version1": version1_id,
            "version2": version2_id,
            "diff": diff
        }

    def delete_config(
            self,
            service_name: str,
            user_id: Optional[int] = None,
            current_user: Optional[User] = None
    ):
        """Delete a service configuration for the given user.

        Admins may omit user_id to delete globally (or pass a specific user_id).
        """
        db_config = self.get_config(service_name, user_id=user_id, current_user=current_user)

        if not db_config:
            raise HTTPException(status_code=404, detail="Service config not found")

        self.db.delete(db_config)
        self.db.commit()
        return True

    def rollback_to_version(
            self,
            service_name: str,
            target_version_id: int,
            user_id: Optional[int] = None,
            current_user: Optional[User] = None,
    ):
        """Rollback the current configuration to a specified previous version.

        - Admins: may pass user_id or omit to rollback the first match across users for the service.
        - Non-admins: user_id is required and must match the caller (enforced via routes typically).
        """
        # Determine scoping based on role
        is_admin = self._is_admin(current_user)

        # Locate target version with appropriate scoping
        version_query = self.db.query(ConfigVersion).filter_by(service_name=service_name)
        if is_admin:
            if user_id is not None:
                version_query = version_query.filter_by(user_id=user_id)
            # else admin without user_id: no extra filter
        else:
            if user_id is None:
                raise HTTPException(status_code=400, detail="user_id is required for non-admin operations")
            version_query = version_query.filter_by(user_id=user_id)

        target_version = version_query.filter_by(id=target_version_id).first()
        if not target_version:
            raise HTTPException(status_code=404, detail="Version not found")

        effective_user_id = target_version.user_id

        # Fetch current active config for the same owner
        current_config = (
            self.db.query(ServiceConfig)
            .filter_by(name=service_name, user_id=effective_user_id)
            .first()
        )
        if not current_config:
            raise HTTPException(status_code=404, detail="Active config not found")

        # Apply rollback and persist
        current_config.config = target_version.config
        self.db.commit()
        self.db.refresh(current_config)

        # Add new version entry documenting the rollback snapshot
        self.add_new_version(service_name, target_version.config, effective_user_id)

        # Return the ORM object so response_model=ConfigResponse can serialize it
        return current_config
