from fastapi import FastAPI
import fastapi_cdn_host
import os

from app.db import models
from app.db.database import engine
from app.api.routes_config import router as config_router
from app.api.auth import router as auth
from app.core.config import settings

app = FastAPI(
    title="ConfigSync",
    description="Centralized configuration management service",
    version="1.0.0"
)

# Patch to serve swagger UI resources locally
fastapi_cdn_host.patch_docs(app)

@app.on_event("startup")
def on_startup():
    # Skip database creation during tests - tests manage their own DB
    if os.getenv("TESTING") != "true":
        models.Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}!",
        "database": settings.DATABASE_URL
    }

# Register routes
app.include_router(config_router)
app.include_router(auth)



