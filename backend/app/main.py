"""FastAPI application factory for the Destiny computation API.

Ordinary calculations are stateless. Manual report fulfilment separately stores
fixed documents for expiry, re-fetch and revocation; raw birth inputs are not
retained by that store. Browser archives are local, without E2EE.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers

API_DESCRIPTION = (
    "Cross-civilization divination computation API. All results are produced by "
    "authoritative libraries (lunar-python, Swiss Ephemeris) or curated content "
    "datasets; nothing is mocked. For entertainment and cultural reference only."
)


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    settings = get_settings()

    app = FastAPI(
        title="Destiny API",
        version="0.1.0",
        description=API_DESCRIPTION,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)
    app.include_router(api_router)

    @app.get("/api/v1/health", tags=["meta"], summary="Liveness probe")
    async def health() -> dict[str, str]:
        """Report service liveness."""
        return {"status": "ok", "service": "destiny-backend"}

    return app


app = create_app()
