"""卡巴拉生命之树 (Kabbalah) HTTP adapter (thin layer over the engine).

Two routes: ``GET /tree`` serves the whole fixed reference map (the frontend caches
it as static content), and ``POST /gematria`` folds an optional word onto that map.
"""

from fastapi import APIRouter

from app.engines.kabbalah import build_tree, compute_gematria
from app.schemas.kabbalah import GematriaReading, GematriaRequest, KabbalahTree

router = APIRouter(prefix="/kabbalah")


@router.get("/tree", response_model=KabbalahTree, summary="Fetch the full Tree of Life map")
async def kabbalah_tree() -> KabbalahTree:
    """返回完整的生命之树：三柱、四界、十原质（含隐藏的 Daath）与 22 路径。

    The map is fixed Golden Dawn content, not a computation, so it is served as a
    cacheable GET; the frontend renders and explores it client-side.
    """
    return build_tree()


@router.post("/gematria", response_model=GematriaReading, summary="Fold a word onto the Tree via gematria")
async def kabbalah_gematria(request: GematriaRequest) -> GematriaReading:
    """以英文 gematria 称量一个词，折入固定的十原质与 22 路径，返回数理落点与释义。

    Latin letters are weighed (A=1…Z=26); a word with none raises a 422
    ``gematria_no_latin_letters`` domain error rather than returning an empty fold.
    """
    return compute_gematria(request.text)
