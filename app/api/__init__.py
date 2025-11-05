# app.api package initializer
# Keep this module lightweight to avoid importing routers at package import time.
# Import specific routers where needed, e.g. `from app.api import auth` or
# `from app.api.routes_config import router`.

__all__ = []
