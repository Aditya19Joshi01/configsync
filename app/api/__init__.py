# app.api package initializer
# Exposes API routers for the application.
from .auth import router as auth_router
from .routes_config import router as config_router

__all__ = ["auth_router", "config_router"]

