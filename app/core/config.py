from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = Field(default="gmail-job-tracker", alias="APP_NAME")
    environment: str = Field(default="dev", alias="ENVIRONMENT")
    api_prefix: str = Field(default="/api", alias="API_PREFIX")

    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=120, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/gmail_job_tracker",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    auto_create_tables: bool = Field(default=False, alias="AUTO_CREATE_TABLES")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    gmail_client_secret_json: str | None = Field(default=None, alias="GMAIL_CLIENT_SECRET_JSON")
    gmail_token_json: str | None = Field(default=None, alias="GMAIL_TOKEN_JSON")
    gmail_scopes: str = Field(
        default="https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.modify",
        alias="GMAIL_SCOPES",
    )
    gmail_poll_interval_minutes: int = Field(default=10, alias="GMAIL_POLL_INTERVAL_MINUTES")
    daily_digest_hour_utc: int = Field(default=8, alias="DAILY_DIGEST_HOUR_UTC")


settings = Settings()  # type: ignore[call-arg]
