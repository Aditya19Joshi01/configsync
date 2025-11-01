from sqlalchemy.orm import Session
from app.db.models import ServiceConfig
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
            .filter(ServiceConfig.name == service_name)
            .first()
        )

    def update_config(self, data: ConfigUpdateSchema):
        """
        Update the config if it exists, otherwise create a new one.
        Returns the latest ServiceConfig object.
        """
        config = self.get_config(data.name)
        if config:
            config.config = data.config
        else:
            config = ServiceConfig(name=data.name, config=data.config)
            self.db.add(config)

        self.db.commit()
        self.db.refresh(config)
        return config
