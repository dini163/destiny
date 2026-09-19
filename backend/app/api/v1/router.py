"""Aggregator for all v1 sub-routers.

Each divination system lives in its own module (``api/v1/<system>.py``) and is
included here, keeping ``main.py`` stable as systems are added.
"""

from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")

# System sub-routers are included below as they are implemented, e.g.:
#   from app.api.v1 import bazi, western, tarot, zhouyi, meta
#   api_router.include_router(meta.router, tags=["meta"])
