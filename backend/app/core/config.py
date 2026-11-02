"""Application settings loaded from environment variables or a .env file."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Destiny backend.

    Values are read from environment variables (upper-snake case) and, as a
    fallback, from a local ``.env`` file. See ``.env.example`` at repo root.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173"
    sweph_ephe_path: str = ""
    app_environment: Literal["development", "test", "production"] = "development"
    report_store_path: str = "data/local/report-deliveries.sqlite3"
    report_operator_key: str = ""
    #: 报告签名链接的密钥与有效期（小时）。密钥只从环境变量读；开发占位值生产必须替换
    #: （见 app/core/report_orders.py 的安全说明与根目录 .env.example）。
    report_secret: str = "dev-report-secret-change-me"
    report_link_ttl_hours: int = Field(default=168, ge=1, le=8760)

    @model_validator(mode="after")
    def validate_production_secrets(self):
        """A copied development environment must fail closed at production startup."""
        if self.app_environment == "production" and (
            self.report_secret == "dev-report-secret-change-me"
            or len(self.report_secret.encode("utf-8")) < 32
            or len(set(self.report_secret)) < 12
        ):
            raise ValueError(
                "Production requires a random REPORT_SECRET; generate it with secrets.token_hex(32)."
            )
        if self.report_operator_key and (
            len(self.report_operator_key.encode("utf-8")) < 32
            or self.report_operator_key == self.report_secret
        ):
            raise ValueError(
                "REPORT_OPERATOR_KEY must be an independent random secret of at least 32 bytes."
            )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS origins parsed from the comma-separated ``cors_origins`` string."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide cached Settings instance."""
    return Settings()
