"""三才配置的措辞表 —— 只存"关系怎么说"，关系本身归五行图。

spec 决策四：不引入 125 行手抄三才吉凶表。天/人/地三格的五行两两之间只有五种关系
（生我 / 我生 / 克我 / 我克 / 比和），图在 `content/wuxing.py`（八字与六爻已在用），
这里只把关系说成一句可核对的话。句子取自通行姓名学对三才生克的表述，属整理措辞。
"""

from __future__ import annotations

from dataclasses import dataclass

from app.content.wuxing import CONTROLLED_BY, CONTROLS, GENERATED_BY, GENERATES

#: 措辞是整理物，不是某本古籍的原话，出处必须自认。
SANCAI_SOURCE = "三才配置生克关系（依五行生克图推导，措辞为通行姓名学整理，非古籍原文）"


@dataclass(frozen=True)
class SancaiRelation:
    key: str
    sentence: str
    source: str


SANCAI_RELATIONS: dict[str, SancaiRelation] = {
    "生我": SancaiRelation("生我", "前者生助后者，得扶持之势，根基受养。", SANCAI_SOURCE),
    "我生": SancaiRelation("我生", "前者泄气以生后者，付出多而自守薄。", SANCAI_SOURCE),
    "克我": SancaiRelation("克我", "后者制约前者，受制则有抑塞之象。", SANCAI_SOURCE),
    "我克": SancaiRelation("我克", "前者克制后者，能任其事而需费力。", SANCAI_SOURCE),
    "比和": SancaiRelation("比和", "两者五行同类，气性相通而少乖违。", SANCAI_SOURCE),
}


def relation_between(from_element: str, to_element: str) -> str:
    """以 `from_element` 为"我"，说它对 `to_element` 的关系。"""
    if from_element == to_element:
        return "比和"
    if GENERATES[from_element] == to_element:
        return "我生"
    if GENERATED_BY[from_element] == to_element:
        return "生我"
    if CONTROLS[from_element] == to_element:
        return "我克"
    if CONTROLLED_BY[from_element] == to_element:
        return "克我"
    raise ValueError(f"未知五行：{from_element} / {to_element}")
