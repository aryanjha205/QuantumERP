from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Union


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Native Voice ERP Platform"
    API_V1_STR: str = "/api/v1"

    DEBUG: bool = False

    SECRET_KEY: str = "your-super-secret-key-that-should-be-changed"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # CORS — allow all by default; override via env var in production
    # Keep ``str`` in the input annotation so pydantic-settings does not require
    # an environment value to be JSON before this validator can normalize it.
    # This lets Vercel use either ``https://example.com`` or a JSON array.
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "https://quant-urp.vercel.app",
        "http://localhost:3000",
        "http://localhost:5500",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)

    # Database — set SQLALCHEMY_DATABASE_URI directly via Vercel env var
    SQLALCHEMY_DATABASE_URI: str = ""

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def normalize_database_uri(cls, value: str) -> str:
        """Accept a database URL pasted from either a .env file or Vercel."""
        if not isinstance(value, str):
            return value

        value = value.strip()
        # Quotes are syntax in a .env file, but are literal characters in
        # Vercel's environment-variable editor.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        # Also tolerate pasting a complete .env assignment in the Value field.
        prefix = "SQLALCHEMY_DATABASE_URI="
        if value.startswith(prefix):
            value = value[len(prefix):].strip().strip("'\"")
        return value

    # Redis (not used in serverless; kept for local dev)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: str = "6379"

    # SMTP Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
