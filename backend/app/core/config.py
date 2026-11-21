from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-level settings, read from environment variables.

    Any value can be overridden with a VARCITY_ prefixed variable,
    e.g. VARCITY_ENVIRONMENT=production, or from a .env file.
    """

    app_name: str = "Varcity"
    version: str = "0.1.0"
    environment: str = "development"

    # Required: the app refuses to start without these.
    database_url: str
    # Signs CSRF tokens. Keep it secret and unique per installation.
    secret_key: str = Field(min_length=32)

    # Sessions and cookies
    session_cookie_name: str = "varcity_session"
    session_idle_minutes: int = 30
    session_absolute_hours: int = 12
    # Must be True in production (HTTPS). False allows http://localhost in development.
    cookie_secure: bool = False

    # Variables the app doesn't know about (such as the test database URL,
    # which only the test suite uses) are ignored.
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="VARCITY_", extra="ignore"
    )


settings = Settings()