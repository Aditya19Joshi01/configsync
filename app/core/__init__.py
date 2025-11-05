# app.core package initializer
# Expose core utilities and settings
from .config import settings

# NOTE: Do NOT import .security here. Importing security at package import time
# causes a circular import: security imports app.db.get_db which may not be
# available while app.db is being initialized. Import security symbols where
# needed (e.g. `from app.core import security`) instead.

__all__ = ["settings"]
