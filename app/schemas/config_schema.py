from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime


class ConfigUpdateSchema(BaseModel):
    """
    Schema for incoming requests to update or create a config.
    """
    name: str
    config: Dict[str, Any]


class ConfigResponse(BaseModel):
    """
    Schema for sending config data back in API responses.
    """
    id: int
    name: str
    config: Dict[str, Any]
    updated_at: datetime

    class Config:
        from_attributes = True  # Enables compatibility with SQLAlchemy models (Pydantic v2)
