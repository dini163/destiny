"""把任意干支合成成一根完整柱：流年、流月、合婚盘都走这条路（spec §5）。

`bazi.py:_build_pillar` 只吃 `EightChar`，而岁运柱的来源是两个字的字符串，所以这里
逐项回查权威表自己拼一次；两者必须逐字段相等，已由 `tests/test_bazi_pillar.py` 的
24 柱对拍钉住。唯一的例外是日柱的 `shishen_gan`：命盘把日干自身的十神记作 `日主`，
那是本命柱专属称谓，岁运柱永远不是日主，所以合成柱照十神表记 `比肩`。

表全部来自 `lunar_python.util.LunarUtil`（注意：它不在包顶层，`from lunar_python
import LunarUtil` 会 ImportError）与 `app.content`，本模块不新增历法假设。
"""

from lunar_python.util import LunarUtil

from app.content.bazi_changsheng import di_shi
from app.content.bazi_nayin import nayin_meaning
from app.content.wuxing import GAN_ELEMENT, ZHI_ELEMENT
from app.schemas.bazi import BaziPillar

GAN_ORDER = "甲乙丙丁戊己庚辛壬癸"


def build_transit_pillar(
    ganzhi: str, *, position: str, label: str, day_master: str
) -> BaziPillar:
    """任意干支 + 给定日主 → 一根完整柱。字符不在表内即报错，不静默给空值。"""
    if len(ganzhi) != 2 or LunarUtil.getJiaZiIndex(ganzhi) < 0:
        raise ValueError(f"非法干支：{ganzhi!r}（须为天干一字 + 地支一字，且落在六十甲子内）")
    if day_master not in GAN_ORDER:
        raise ValueError(f"非法日主：{day_master!r}")
    gan, zhi = ganzhi[0], ganzhi[1]
    hidden_stems = list(LunarUtil.ZHI_HIDE_GAN[zhi])
    return BaziPillar(
        position=position,
        label=label,
        ganzhi=ganzhi,
        gan=gan,
        zhi=zhi,
        gan_element=GAN_ELEMENT[gan],
        zhi_element=ZHI_ELEMENT[zhi],
        nayin=nayin_meaning(ganzhi).nayin,
        hidden_stems=hidden_stems,
        hidden_stem_elements=[GAN_ELEMENT[stem] for stem in hidden_stems],
        shishen_gan=LunarUtil.SHI_SHEN[day_master + gan],
        shishen_zhi=[LunarUtil.SHI_SHEN[day_master + stem] for stem in hidden_stems],
        di_shi=di_shi(day_master, zhi),
        xun=LunarUtil.getXun(ganzhi),
        xun_kong=LunarUtil.getXunKong(ganzhi),
    )
