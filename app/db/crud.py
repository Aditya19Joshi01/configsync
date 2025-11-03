from sqlalchemy.orm import Session
from app.db.models import ServiceConfig, ConfigVersion
from app.schemas.config_schema import ConfigUpdateSchema


class ConfigRepository:
    """
    Handles all database operations related to service configurations.
    Acts as an abstraction layer between the DB and business logic.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_config(self, service_name: str):
        """Fetch the configuration for a given service."""
        return (
            self.db.query(ServiceConfig)
            .filter_by(name=service_name)
            .first()
        )

    def update_or_create_config(self, data: ConfigUpdateSchema | None = None, config_data: ConfigUpdateSchema | None = None):
        """Update existing config or create a new one.

        Accepts either `data` (current callers) or `config_data` (legacy callers / static analysis expectations).
        """
        input_data = data or config_data
        if input_data is None:
            raise ValueError("No configuration data provided to update_or_create_config")

        db_config = self.get_config(input_data.name)

        if db_config:
            db_config.config = input_data.config
            self.db.commit()
            self.db.refresh(db_config)
        else:
            db_config = ServiceConfig(name=input_data.name, config=input_data.config)
            self.db.add(db_config)
            self.db.commit()
            self.db.refresh(db_config)

        # Add a version entry for history
        self.add_new_version(input_data.name, input_data.config)
        return db_config

    def get_latest_version(self, service_name: str):
        """Fetch the latest configuration version for a given service."""
        db = self.db
        return (
            db.query(ConfigVersion)
            .filter_by(service_name=service_name)
            .order_by(ConfigVersion.version.desc())
            .first()
        )

    def add_new_version(self, service_name: str, config: dict):
        """Add a new configuration version for a given service."""
        latest_version = self.get_latest_version(service_name)
        new_version_number = (
            latest_version.version + 1 if latest_version else 1
        )

        new_version = ConfigVersion(
            service_name=service_name,
            version=new_version_number,
            config=config,
        )
        self.db.add(new_version)
        self.db.commit()
        self.db.refresh(new_version)
        return new_version

    def list_versions(self, service_name: str):
        """List all configuration versions for a given service."""
        db = self.db
        return (
            db.query(ConfigVersion)
            .filter_by(service_name=service_name)
            .order_by(ConfigVersion.version.desc())
            .all()
        )