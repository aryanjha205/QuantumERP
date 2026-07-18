from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator
from typing import List, Union


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Native Voice ERP Platform"
    API_V1_STR: str = "/api/v1"

    DEBUG: bool = False

    SECRET_KEY: str = "your-super-secret-key-that-should-be-changed"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # CORS — allow all by default; override via env var in production
    BACKEND_CORS_ORIGINS: List[str] = [
        "https://quant-urp.vercel.app",
        "http://localhost:3000",
        "http://localhost:5500",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database — set SQLALCHEMY_DATABASE_URI directly via Vercel env var
    SQLALCHEMY_DATABASE_URI: str = ""

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "erp_user"
    POSTGRES_PASSWORD: str = "erp_password"
    POSTGRES_DB: str = "erp_db"
    POSTGRES_PORT: str = "5432"

    @model_validator(mode="after")
    def assemble_db_connection(self) -> "Settings":
        if not self.SQLALCHEMY_DATABASE_URI:
            self.SQLALCHEMY_DATABASE_URI = (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return self

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
