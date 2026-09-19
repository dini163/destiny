"""Aggregator for all v1 sub-routers.

Each divination system lives in its own module (``api/v1/<system>.py``) and is
included here, keeping ``main.py`` stable as systems are added.
"""

from fastapi import APIRouter

from app.api.v1 import bazi, meta, tarot, western

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(meta.router, tags=["meta"])
api_router.include_router(bazi.router, tags=["bazi"])
api_router.include_router(western.router, tags=["western"])
api_router.include_router(tarot.router, tags=["tarot"])

# System sub-routers are included below as they are implemented, e.g.:
#   api_router.include_router(zhouyi.router, tags=["zhouyi"])
