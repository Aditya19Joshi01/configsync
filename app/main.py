from fastapi import FastAPI

from app.db import models
from app.db.database import engine
from app.api.routes_config import router as config_router
from app.core.config import settings

app = FastAPI(
    title="ConfigSync",
    description="Centralized configuration management service",
    version="1.0.0"
)

@app.on_event("startup")
def on_startup():
    models.Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}!",
        "database": settings.DATABASE_URL
    }

# Register routes
app.include_router(config_router)



