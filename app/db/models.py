from sqlalchemy import Column, Integer, String, JSON, DateTime, func
from datetime import datetime
from app.db.database import Base

class ServiceConfig(Base):
    """
    Represents configuration data for each service.
    """
    __tablename__ = "service_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    config = Column(JSON, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

class ConfigVersion(Base):
    __tablename__ = "config_versions"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String, index=True)
    version = Column(Integer)
    config = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
