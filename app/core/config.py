from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ConfigSync"
    DATABASE_URL: str = "sqlite:///./configsync.db"
    API_KEY: str = "supersecretkey"

    model_config = SettingsConfigDict(
        env_file=".env",  # Optional file for environment variables
        case_sensitive=True
    )

# Create a global settings object
settings = Settings()