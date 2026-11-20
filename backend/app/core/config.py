from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-level settings, read from environment variables.

    Any value can be overridden with a VARCITY_ prefixed variable,
    e.g. VARCITY_ENVIRONMENT=production, or from a .env file.
    """

    app_name: str = "Varcity"
    version: str = "0.1.0"
    environment: str = "development"

    # Required: the app refuses to start without it.
    database_url: str

    # Variables the app doesn't know about (such as the test database URL,
    # which only the test suite uses) are ignored.
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="VARCITY_", extra="ignore"
    )


settings = Settings()