from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "ConfigSync"
    # Default to the Postgres service provided by docker-compose. This can be
    # overridden by setting the DATABASE_URL environment variable or by using
    # a .env file.
    DATABASE_URL: str = "postgresql+psycopg2://configsync:configsync@db:5432/configsync"
    API_KEY: str = "supersecretkey"

    model_config = SettingsConfigDict(
        env_file=".env",  # Optional file for environment variables
        case_sensitive=True
    )

# Create a global settings object
settings = Settings()