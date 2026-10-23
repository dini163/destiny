"""Application settings loaded from environment variables or a .env file."""

from functools import lru_cache

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
    #: 报告签名链接的密钥与有效期（小时）。密钥只从环境变量读；开发占位值生产必须替换
    #: （见 app/core/report_orders.py 的安全说明与根目录 .env.example）。
    report_secret: str = "dev-report-secret-change-me"
    report_link_ttl_hours: int = 168

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS origins parsed from the comma-separated ``cors_origins`` string."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide cached Settings instance."""
    return Settings()
