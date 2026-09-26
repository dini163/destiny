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

from app.content import CONTENT_VERSION
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
from app.core.errors import GematriaInputError
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


def _sephirah_node(s: Sephirah) -> SephirahNode:
    pillar = PILLARS[s.pillar]
    return SephirahNode(
        number=s.number,
        id=s.id,
        name_hebrew=s.name_hebrew,
        name=s.name,
        name_zh=s.name_zh,
        meaning=s.meaning,
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
        provenance=KabbalahProvenance(
            engine="kabbalah-tree",
            content_version=CONTENT_VERSION,
            source=KABBALAH_SOURCE,
            note=TREE_NOTE,
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
        ),
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
    return (
        f"「{normalized}」的英文 ordinal 数值为 {ordinal}（reduction {reduction}，数根 {root}）。"
        f"折入生命之树，它相应于第 {sephirah.number} 原质【{sephirah.name_zh} {sephirah.name_hebrew} · "
        f"{sephirah.pillar_name_zh} · {sephirah.sphere}】——{sephirah.meaning}"
        f"又连于第 {path.number} 路径【{path.letter_zh} {path.letter}（{path.letter_value}）· "
        f"{path.tarot_zh} {path.tarot_numeral} · {path.correspondence}】——{path.meaning}"
        f"两相参详：此名之数理落点，提示由「{path.from_name_zh}」经「{path.tarot_zh}」之路，"
        f"趋近「{sephirah.name_zh}」之境的功课。"
    )
