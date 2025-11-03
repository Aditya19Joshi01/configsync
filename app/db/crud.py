from sqlalchemy.orm import Session
from app.db.models import ServiceConfig, ConfigVersion
from app.schemas.config_schema import ConfigUpdateSchema


class ConfigRepository:
    """
    Handles all database operations related to service configurations.
    Acts as an abstraction layer between the DB and business logic.
    Now scoped to a user via user_id to ensure users only see their own configs.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_config(self, service_name: str, user_id: int):
        """Fetch the configuration for a given service belonging to user."""
        return (
            self.db.query(ServiceConfig)
            .filter_by(name=service_name, user_id=user_id)
            .first()
        )

    def update_or_create_config(self, data: ConfigUpdateSchema | None = None, config_data: ConfigUpdateSchema | None = None, user_id: int | None = None):
        """Update existing config or create a new one for the given user.

        Accepts either `data` (current callers) or `config_data` (legacy callers / static analysis expectations).
        """
        input_data = data or config_data
        if input_data is None:
            raise ValueError("No configuration data provided to update_or_create_config")
        if user_id is None:
            raise ValueError("user_id is required to scope config operations")

        db_config = self.get_config(input_data.name, user_id)

        if db_config:
            db_config.config = input_data.config
            self.db.commit()
            self.db.refresh(db_config)
        else:
            db_config = ServiceConfig(name=input_data.name, config=input_data.config, user_id=user_id)
            self.db.add(db_config)
            self.db.commit()
            self.db.refresh(db_config)

        # Add a version entry for history
        self.add_new_version(input_data.name, input_data.config, user_id)
        return db_config

    def get_latest_version(self, service_name: str, user_id: int):
        """Fetch the latest configuration version for a given service for the user."""
        db = self.db
        return (
            db.query(ConfigVersion)
            .filter_by(service_name=service_name, user_id=user_id)
            .order_by(ConfigVersion.version.desc())
            .first()
        )

    def add_new_version(self, service_name: str, config: dict, user_id: int):
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

    def list_versions(self, service_name: str, user_id: int):
        """List all configuration versions for a given service for the user."""
        db = self.db
        return (
            db.query(ConfigVersion)
            .filter_by(service_name=service_name, user_id=user_id)
            .order_by(ConfigVersion.version.desc())
            .all()
        )

    def list_all_configs_for_user(self, user_id: int):
        """Helper to list all current service configs for the user."""
        return (
            self.db.query(ServiceConfig)
            .filter_by(user_id=user_id)
            .all()
        )
