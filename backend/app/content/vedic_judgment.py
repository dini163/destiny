"""吠陀九曜自然吉凶与擢升/陷落判定表（verdict 判定层的锚；通行经典可署名，平台自撰归纳）。

仓内原本没有任何尊贵/吉凶表（Plan H R48 刻意不建庙旺落陷，见 `engines/plain_corpora.py`
VEDIC 登记注）。本表为结论卡片新立：自然吉凶分类与擢升（Uchcha）/陷落（Neecha）星座，
分类依据《Brihat Parashara Hora Shastra》（《布里哈特·帕拉沙拉·霍拉·夏斯特拉》）的
行星性质章（Graha Svabhava，九曜自然吉凶）与擢升陷落章（Uchcha/Neecha）通行论述，
由平台按章归纳成表，不是古籍逐字引文（R46 自撰 + 诚实双署：到章不到书 + 自撰声明）。

罗睺/计都的擢升陷落各宗派略有出入，本表取通行的「罗睺擢升金牛、陷落天蝎；计都擢升天蝎、
陷落金牛」一说，并在出处串里说破这是宗派通行说，不冒充唯一定论。
"""

from dataclasses import dataclass

#: 自然吉凶归类依据的经典章（到章不到书）。
_SVABHAVA_CHAPTER = "《Brihat Parashara Hora Shastra》行星性质章（Graha Svabhava）"
_DIGNITY_CHAPTER = "《Brihat Parashara Hora Shastra》擢升陷落章（Uchcha / Neecha）"

#: 登记表（`content/__init__.py::VEDIC_CONTENT_SOURCES`）用的书级出处串：经典章 + 自撰双署。
JUDGMENT_SOURCE = (
    "依《Brihat Parashara Hora Shastra》行星性质章与擢升陷落章通行论述、由平台自撰归纳的"
    "九曜自然吉凶与擢升/陷落星座表，不是古籍逐字引文；不构成医疗、法律、财务建议。"
)


@dataclass(frozen=True)
class GrahaQuality:
    """一曜的自然吉凶（不因落座/相位而变的天性）。"""

    name: str          # 与 `content/vedic.py::GRAHAS` 的 English key 一致
    name_zh: str
    quality: str       # "benefic" | "neutral" | "malefic"
    source: str


#: 自然吉星：木星（Guru）、金星（Shukra）。
#: 中性：太阳、太阴、水星——吉凶随联结与落座而变，本表不归入吉或凶。
#: 自然凶星：火星、土星、罗睺、计都。
NATURAL_QUALITY: tuple[GrahaQuality, ...] = (
    GrahaQuality("Jupiter", "木星", "benefic", f"{_SVABHAVA_CHAPTER}·木星为吉"),
    GrahaQuality("Venus", "金星", "benefic", f"{_SVABHAVA_CHAPTER}·金星为吉"),
    GrahaQuality("Sun", "太阳", "neutral", f"{_SVABHAVA_CHAPTER}·太阳依条件而定"),
    GrahaQuality("Moon", "太阴", "neutral", f"{_SVABHAVA_CHAPTER}·太阴依条件而定"),
    GrahaQuality("Mercury", "水星", "neutral", f"{_SVABHAVA_CHAPTER}·水星随联结而定"),
    GrahaQuality("Mars", "火星", "malefic", f"{_SVABHAVA_CHAPTER}·火星为凶"),
    GrahaQuality("Saturn", "土星", "malefic", f"{_SVABHAVA_CHAPTER}·土星为凶"),
    GrahaQuality("Rahu", "罗睺", "malefic", f"{_SVABHAVA_CHAPTER}·罗睺为凶"),
    GrahaQuality("Ketu", "计都", "malefic", f"{_SVABHAVA_CHAPTER}·计都为凶"),
)

QUALITY_BY_NAME: dict[str, GrahaQuality] = {row.name: row for row in NATURAL_QUALITY}


@dataclass(frozen=True)
class Dignity:
    """一曜的擢升/陷落星座（整宫制只比星座序，不取度数细分）。"""

    name: str
    exaltation: int    # sign_index，0 = Mesha（白羊）
    debilitation: int  # sign_index
    source: str


#: 星座序 0-11 = Mesha/Vrishabha/Mithuna/Karka/Simha/Kanya/Tula/Vrischika/Dhanu/Makara/Kumbha/Meena。
DIGNITY: tuple[Dignity, ...] = (
    Dignity("Sun", 0, 6, f"{_DIGNITY_CHAPTER}·太阳擢升白羊、陷落天秤"),
    Dignity("Moon", 1, 7, f"{_DIGNITY_CHAPTER}·太阴擢升金牛、陷落天蝎"),
    Dignity("Mars", 9, 3, f"{_DIGNITY_CHAPTER}·火星擢升摩羯、陷落巨蟹"),
    Dignity("Mercury", 5, 11, f"{_DIGNITY_CHAPTER}·水星擢升处女、陷落双鱼"),
    Dignity("Jupiter", 3, 9, f"{_DIGNITY_CHAPTER}·木星擢升巨蟹、陷落摩羯"),
    Dignity("Venus", 11, 5, f"{_DIGNITY_CHAPTER}·金星擢升双鱼、陷落处女"),
    Dignity("Saturn", 6, 0, f"{_DIGNITY_CHAPTER}·土星擢升天秤、陷落白羊"),
    Dignity("Rahu", 1, 7, f"{_DIGNITY_CHAPTER}·罗睺擢升金牛、陷落天蝎（宗派通行说）"),
    Dignity("Ketu", 7, 1, f"{_DIGNITY_CHAPTER}·计都擢升天蝎、陷落金牛（宗派通行说）"),
)

DIGNITY_BY_NAME: dict[str, Dignity] = {row.name: row for row in DIGNITY}

# --- 结论卡片（verdict）框架句：全部受控，引擎只填槽，不现编中文 -----------------
#: 本系统无页面档位词，档位走共享五档（`engines/verdict.GRADE_BANDS`）。

VERDICT_OUTLOOK: dict[str, str] = {
    "大吉": "吉星得位，局面顺承",
    "吉": "吉星居多，顺势可成",
    "平": "吉凶相抵，不偏不倚",
    "小凶": "凶星偏重，宜守不宜进",
    "凶": "多曜失势，先稳住基本盘",
}

VERDICT_SUMMARY_FRAME = (
    "此盘星曜属{grade}：自然吉星{benefic}颗、自然凶星{malefic}颗，"
    "擢升{exalted}颗、陷落{debased}颗，{outlook}。"
)

VERDICT_ADVICE: dict[str, str] = {
    "大吉": "势头正盛可放手去做，得志时仍要给边界留余地。",
    "吉": "吉星居多值得把握，推进时留意失势曜划出的边界。",
    "平": "吉凶相抵不必强求，先把眼前一步走稳再谈进展。",
    "小凶": "凶星偏重不宜冒进，先守住脚下，等局面松动再动。",
    "凶": "此时宜守不宜攻，先把基本盘稳住，不做重大决断。",
}
