"""Aggregator for all v1 sub-routers.

Each divination system lives in its own module (``api/v1/<system>.py``) and is
included here, keeping ``main.py`` stable as systems are added.
"""

from fastapi import APIRouter

from app.api.v1 import bazi, kabbalah, lenormand, meihua, meta, name, numerology, qimen, runes, synastry, tarot, transit, vedic, western, ziwei, zhouyi

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(meta.router, tags=["meta"])
api_router.include_router(bazi.router, tags=["bazi"])
api_router.include_router(western.router, tags=["western"])
api_router.include_router(tarot.router, tags=["tarot"])
api_router.include_router(zhouyi.router, tags=["zhouyi"])
api_router.include_router(meihua.router, tags=["meihua"])
api_router.include_router(ziwei.router, tags=["ziwei"])
api_router.include_router(qimen.router, tags=["qimen"])
api_router.include_router(lenormand.router, tags=["lenormand"])
api_router.include_router(kabbalah.router, tags=["kabbalah"])
api_router.include_router(transit.router, tags=["transit"])
api_router.include_router(synastry.router, tags=["synastry"])
api_router.include_router(vedic.router, tags=["vedic"])
api_router.include_router(name.router, tags=["name"])
api_router.include_router(numerology.router, tags=["numerology"])
api_router.include_router(runes.router, tags=["runes"])

# Phase-1 MVP systems plus 姓名学、数字命理、北欧卢恩、紫微、奇门、雷诺曼、卡巴拉、行运推运、吠陀占星、
# 西洋合盘 are mounted. Any later-phase system is added here in the same way as it is implemented.
