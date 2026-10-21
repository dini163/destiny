"""卡巴拉生命之树 (Kabbalah) engine — the fixed Tree plus a gematria fold.

Two pure functions over :mod:`app.content.kabbalah`:

* :func:`build_tree` assembles the whole reference map (三柱 / 四界 / 十原质 + 隐藏的
  Daath / 22 路径) exactly as curated — no draw, no randomness, nothing invented.
* :func:`compute_gematria` weighs a word with English ordinal gematria and folds the
  total onto that fixed map by modular arithmetic, then composes a reading from the
  matched Sephirah and Path's real meanings. The fold is clearly labelled a modern
  numerological correspondence, not a traditional decree.

Latin letters only; a word with none raises :class:`GematriaInputError` (the engine
owns the "gematria is defined on the Latin alphabet" premise, exactly as
:class:`NumerologyInputError` does for 数字命理).
"""

from app.content import CONTENT_VERSION, KABBALAH_CONTENT_SOURCES
from app.content.kabbalah import (
    DAATH,
    KABBALAH_SOURCE,
    PATHS,
    PILLARS,
    SEPHIROTH,
    WORLDS,
    Path,
    Sephirah,
    get_path,
    get_sephirah,
)
from app.content.kabbalah_plain import KABBALAH_OVERVIEW_KEYS, KABBALAH_OVERVIEW_TITLES
from app.core.errors import GematriaInputError
# 同层 engines 互引合规，见 `app/engines/synastry.py`、`app/engines/meihua.py` 的既有做法。
from app.engines.plain_compose import overview, reading
from app.engines.plain_corpora import KABBALAH
from app.schemas.common import PlainSection, ProvenanceTable
from app.schemas.kabbalah import (
    GematriaReading,
    KabbalahProvenance,
    KabbalahTree,
    LetterValue,
    PathNode,
    PillarInfo,
    SephirahNode,
)

TREE_NOTE = (
    "生命之树为固定对应图，非随机起盘：十原质、隐藏的 Daath 与 22 路径全部取自策展的"
    "黄金黎明（Golden Dawn）体系，三柱（慈悲 / 严厉 / 平衡）、四界（原型 → 物质）、行星守护、"
    "王徽色、大天使与神名逐条如实回显，未在运行时虚构。坐标 x/y 归一化到 0–1，供前端任意缩放布局。"
    "路径上的塔罗序号从黄金黎明制：力量为 VIII、正义为 XI。"
)

GEMATRIA_NOTE = (
    "gematria 以英文 ordinal（A=1…Z=26）逐字母求和，另附 reduction（每位数字根）与总值的数根；"
    "再以模运算把总值折到固定的十原质与 22 路径上（原质 = (值−1) mod 10 + 1，路径 = (值−1) mod 22 + 11）。"
    "这是一种供冥想的现代数理映射，并非传统卡巴拉的定论断语；命中原质与路径的释义仍取自策展语料，未作虚构。"
    "纯拉丁字母以外的字符（如中文）不计入，若一个拉丁字母也没有则报 gematria_no_latin_letters。"
)


def _tables() -> list[ProvenanceTable]:
    """`KABBALAH_CONTENT_SOURCES` 的第一次被消费（G19）。

    这张登记常量在仓里已经躺了几十天而无人读它（迁移前实测 2026-10-01：
    `grep -rn KABBALAH_CONTENT_SOURCES app/ tests/` → 只命中定义处 `content/__init__.py`），
    本期真读了白话表，就照其它系统的形状把它递进响应，不在引擎里另列一份表名。
    """
    return [
        ProvenanceTable(name=module, version=CONTENT_VERSION, source=source)
        for module, source in KABBALAH_CONTENT_SOURCES
    ]


def _sephirah_node(s: Sephirah) -> SephirahNode:
    pillar = PILLARS[s.pillar]
    return SephirahNode(
        number=s.number,
        id=s.id,
        name_hebrew=s.name_hebrew,
        name=s.name,
        name_zh=s.name_zh,
        meaning=s.meaning,
        plain_meaning=reading(KABBALAH, s.id),
        keywords=list(s.keywords),
        pillar=s.pillar,
        pillar_name_zh=pillar.name_zh,
        world=s.world,
        world_name_zh=WORLDS[s.world],
        sphere=s.sphere,
        color=s.color,
        archangel=s.archangel,
        divine_name=s.divine_name,
        x=s.x,
        y=s.y,
        is_hidden=s.is_hidden,
    )


def _path_node(p: Path) -> PathNode:
    return PathNode(
        number=p.number,
        id=p.id,
        from_sephirah=p.from_sephirah,
        to_sephirah=p.to_sephirah,
        from_name_zh=get_sephirah(p.from_sephirah).name_zh,
        to_name_zh=get_sephirah(p.to_sephirah).name_zh,
        letter=p.letter,
        letter_name=p.letter_name,
        letter_zh=p.letter_zh,
        letter_value=p.letter_value,
        tarot=p.tarot,
        tarot_zh=p.tarot_zh,
        tarot_numeral=p.tarot_numeral,
        correspondence=p.correspondence,
        meaning=p.meaning,
        plain_meaning=reading(KABBALAH, p.id),
    )


def build_tree() -> KabbalahTree:
    """Return the complete Tree of Life reference map."""
    pillars = [
        PillarInfo(id=p.id, name_zh=p.name_zh, name_en=p.name_en, side=p.side, virtue=p.virtue)
        for p in (PILLARS["equilibrium"], PILLARS["mercy"], PILLARS["severity"])
    ]
    return KabbalahTree(
        pillars=pillars,
        worlds=[WORLDS[key] for key in ("atziluth", "bria", "yetzirah", "assiah")],
        sephiroth=[_sephirah_node(s) for s in SEPHIROTH],
        daath=_sephirah_node(DAATH),
        paths=[_path_node(p) for p in PATHS],
        sephirah_count=len(SEPHIROTH),
        path_count=len(PATHS),
        # 整树总论三节：静态、无生辰输入，逐键取语料原文（`reading` 未知键即崩，不兜底）。
        # 次序 = `KABBALAH_OVERVIEW_TITLES` / `KABBALAH_OVERVIEW_KEYS` 的声明序，
        # 由 `tests/golden/test_kabbalah_golden.py` 与页面（J-T7）共同钉住；`_tables()` 不变，
        # 这两个键读的就是 `kabbalah_plain` 那张已经列进清单的表。
        plain=[
            PlainSection(title=title, text=reading(KABBALAH, key))
            for title, key in zip(KABBALAH_OVERVIEW_TITLES, KABBALAH_OVERVIEW_KEYS)
        ],
        provenance=KabbalahProvenance(
            engine="kabbalah-tree",
            content_version=CONTENT_VERSION,
            source=KABBALAH_SOURCE,
            note=TREE_NOTE,
            tables=_tables(),
        ),
    )


def _digital_root(value: int) -> int:
    """Reduce to a single digit 1-9 (0 stays 0)."""
    if value == 0:
        return 0
    return 1 + ((value - 1) % 9)


def compute_gematria(text: str) -> GematriaReading:
    """Weigh ``text`` with English gematria and fold it onto the fixed Tree.

    Raises :class:`GematriaInputError` when the text holds no Latin letters.
    """
    letters = [ch.upper() for ch in text if ch.isascii() and ch.isalpha()]
    if not letters:
        raise GematriaInputError(
            "gematria 依英文字母 A=1…Z=26 称量，此输入没有任何拉丁字母；请改用拉丁拼写（如名字拼音或英文单词）。"
        )

    breakdown = [
        LetterValue(letter=ch, ordinal=ord(ch) - 64, reduction=_digital_root(ord(ch) - 64))
        for ch in letters
    ]
    ordinal = sum(item.ordinal for item in breakdown)
    reduction = sum(item.reduction for item in breakdown)
    root = _digital_root(ordinal)

    sephirah_number = ((ordinal - 1) % 10) + 1
    path_number = ((ordinal - 1) % 22) + 11
    sephirah = _sephirah_node(get_sephirah(sephirah_number))
    path = _path_node(get_path(path_number))

    synthesis = _synthesize("".join(letters), ordinal, reduction, root, sephirah, path)

    return GematriaReading(
        text=text,
        normalized="".join(letters),
        breakdown=breakdown,
        english_ordinal=ordinal,
        english_reduction=reduction,
        digital_root=root,
        sephirah=sephirah,
        path=path,
        synthesis=synthesis,
        provenance=KabbalahProvenance(
            engine="kabbalah-gematria",
            content_version=CONTENT_VERSION,
            source=KABBALAH_SOURCE,
            note=GEMATRIA_NOTE,
            tables=_tables(),
        ),
    )


#: 命名单值总论的框架句（spec §7 的「形状收编」）。**内容一字未改**：这张 frame 是
#: `_synthesize` 原来那串 f-string 逐字改名而来，`G13` 的字面 golden 钉住输出。
#: 之所以必须是有具名槽位的 `overview` 而不是部件列表拼接：`tarot_zh` 与 `name_zh`
#: 在同一句里各出现两次，只有 `frame.format(**parts)` 装得下（裁定 R11）。
#: 白话不进这里（裁定 R4 / G17）：`synthesis` 保持原形状，白话走节点的 `plain_meaning`。
KABBALAH_SYNTHESIS_FRAME = (
    "「{normalized}」的英文 ordinal 数值为 {ordinal}（reduction {reduction}，数根 {root}）。"
    "折入生命之树，它相应于第 {sephirah_number} 原质【{sephirah_name_zh} {sephirah_name_hebrew} · "
    "{sephirah_pillar_name_zh} · {sephirah_sphere}】——{sephirah_meaning}"
    "又连于第 {path_number} 路径【{path_letter_zh} {path_letter}（{path_letter_value}）· "
    "{path_tarot_zh} {path_tarot_numeral} · {path_correspondence}】——{path_meaning}"
    "两相参详：此名之数理落点，提示由「{path_from_name_zh}」经「{path_tarot_zh}」之路，"
    "趋近「{sephirah_name_zh}」之境的功课。"
)


def _synthesize(
    normalized: str,
    ordinal: int,
    reduction: int,
    root: int,
    sephirah: SephirahNode,
    path: PathNode,
) -> str:
    """Compose a reading from the matched Sephirah/Path's real meanings (no fabrication)."""
    return overview(
        KABBALAH_SYNTHESIS_FRAME,
        {
            "normalized": normalized,
            "ordinal": str(ordinal),
            "reduction": str(reduction),
            "root": str(root),
            "sephirah_number": str(sephirah.number),
            "sephirah_name_zh": sephirah.name_zh,
            "sephirah_name_hebrew": sephirah.name_hebrew,
            "sephirah_pillar_name_zh": sephirah.pillar_name_zh,
            "sephirah_sphere": sephirah.sphere,
            "sephirah_meaning": sephirah.meaning,
            "path_number": str(path.number),
            "path_letter_zh": path.letter_zh,
            "path_letter": path.letter,
            "path_letter_value": str(path.letter_value),
            "path_tarot_zh": path.tarot_zh,
            "path_tarot_numeral": path.tarot_numeral,
            "path_correspondence": path.correspondence,
            "path_meaning": path.meaning,
            "path_from_name_zh": path.from_name_zh,
        },
    )
