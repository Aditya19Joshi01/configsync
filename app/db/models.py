from sqlalchemy import Column, Integer, String, JSON, DateTime, func, ForeignKey, UniqueConstraint, Index
from datetime import datetime
from app.db.database import Base

class ServiceConfig(Base):
    """
    Represents configuration data for each service.
    """
    __tablename__ = "service_configs"
    __table_args__ = (
        UniqueConstraint('name', 'user_id', name='uq_service_name_user'),
        Index('ix_service_name_user', 'name', 'user_id'),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    config = Column(JSON, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    # Associate config with a user (owner)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

class ConfigVersion(Base):
    __tablename__ = "config_versions"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String, index=True)
    version = Column(Integer)
    config = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    # Associate version entry with a user (owner)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    __table_args__ = (
        Index('ix_version_service_user', 'service_name', 'user_id'),
    )

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, server_default="user", default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
