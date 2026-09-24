"""毕达哥拉斯数字命理 HTTP 适配器（薄层：只做请求到引擎的映射）。"""

from fastapi import APIRouter

from app.engines.numerology import compute_chart
from app.schemas.numerology import NumerologyChart, NumerologyChartRequest

router = APIRouter(prefix="/numerology")


@router.post(
    "/chart", response_model=NumerologyChart, summary="Derive a pythagorean numerology chart"
)
async def numerology_chart(request: NumerologyChartRequest) -> NumerologyChart:
    """推出六个核心数、四顶峰、四挑战、个人年月日与两套九宫。

    无历法库、无星历、无随机：同输入恒同输出，且每一步约简都进 `steps` 账本，读者拿
    计算器就能复核（spec 决策 5）。响应里**没有 `score`**（决策 14），也没有设计稿那个
    无权威定义的「均衡度百分比」（决策 13）；`provenance.tables` 只列本端点真读到的
    四张语料表。

    分工同 `name.py`：长度类校验归 pydantic（回 FastAPI 的 `detail` 形状），字符集归
    引擎 —— 名字里一个拉丁字母都没有（如纯中文名）过得了长度校验，坏的是「毕达哥拉斯
    1–9 映射定义在 A–Z 上」这条只有引擎知道的前提，故回 422 +
    `numerology_no_latin_letters`，`context` 带上检测到的字符样本，前端据此提示改用
    拼音而不必解析文案。总和为 0 的核心数如实为 null（决策 17），不填 0 充数。
    """
    return compute_chart(
        full_name=request.full_name,
        birth_date=request.birth_date,
        name_zh=request.name_zh,
        reference_date=request.reference_date,
        y_as_vowel=request.y_as_vowel,
    )
