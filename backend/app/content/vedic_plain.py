"""吠陀占星页的白话判语表（Plan H spec §4、§5；恒星盘上的九曜、宫位、宿与主事星）。

**这张表是平台自撰的**，不是任何古籍的转述：吠陀页在仓库里没有一句既有判语可转。
自撰的诚实性支点是另一件事，而且它今天仍然为真：**句子全部预写于表，请求时不生成**。
引擎只按已经算出的九曜位置、整宫宫位、宿位与现行主事星逐条选句，不现编一个字的中文。

**一张表服务多行**（本文件最重要的形状裁定）：
- `vedic.nakshatra.{宿}` 一宿服务九曜与上升共十行（A 手 9 行、B 手 10 行），所以宿条目
  **不点名任何曜**，角色由开篇句说「九曜与上升各自落在……」；
- `vedic.dasha_lord.{曜}` 一颗主事星同时服务大运与小运，所以主事星条目**不写角色词**，
  角色由开篇句说「现行的大运与小运」。
这两条的理由与行运「三层共用一张表」同形：角色一进句子，一张表就得复制成十份或两份，
而复制就是几份互相会漂的判语。

覆盖面 = 页面已印事实的全集（裁定 R47）：九曜落座、九曜落宫、星宿落点（九曜 + 命度）、
现行大运与小运的主事星。条数 = **252** = 108 + 108 + 27 + 9；复测：
`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.engines.plain_corpora import VEDIC; print(len(VEDIC.universe()))"` → 252。
**刻意不建**（spec §5.3 的键式就是这张排除表）：逆行状态、四足（pada）、度数、宿主、
宫主、分盘、庙旺落陷、任何综合分数或吉凶档位收尾句。
"""

from app.content import vedic_plain_gruha

VEDIC_PLAIN_SOURCE = (
    "平台自撰的吠陀白话转述表，把九曜落座、落宫、二十七宿与 Vimshottari 主事的通行语义整理成白话，"
    "逐条对应恒星盘上已经算出的星曜位置、整宫宫位、星宿与现行大运主星。"
    "不是古籍引文，不署任何书名，不构成医疗、法律、财务建议。"
)

#: 页面出处块与吠陀页文案共用的**自撰声明**（F/G 的 R50 同一条，换到吠陀这一家）。
#: 三句、句间「。」、无「；」——`FORBIDDEN` 含「；」，本串与语料同口径，由
#: `tests/content/test_vedic_plain_corpus.py::test_the_source_string_and_the_note_are_provenance_declarations`
#: 自守（出处串与 note 都不进 `wording_violations` 的遍历，谁用谁自守）。
VEDIC_PLAIN_NOTE = (
    "恒星盘上的落座、落宫、星宿与现行大运由瑞士星历与 Vimshottari 定则实时算出，页面先报这些结构事实。"
    "下方的白话逐条转述上面已经算出的九曜位置与主事星，句子全部预先写在自撰语料表里，请求时不生成任何中文。"
    "这张表是平台自撰的通行教义归纳，不是古籍引文，不署任何书名，不构成医疗、法律或财务建议，也不预测具体事件。"
)


def gruha_sign_key(graha: str, sign: str) -> str:
    return f"vedic.gruha_sign.{graha}.{sign}"


def gruha_house_key(graha: str, house: int) -> str:
    return f"vedic.gruha_house.{graha}.{house}"


def nakshatra_key(nakshatra: str) -> str:
    return f"vedic.nakshatra.{nakshatra}"


def dasha_lord_key(graha: str) -> str:
    return f"vedic.dasha_lord.{graha}"


VEDIC_SECTION_TITLES = {
    "gruha_sign": "九曜落座",
    "gruha_house": "九曜落宫",
    "nakshatra": "星宿落点",
    "dasha": "现行大运与小运",
}

#: 唯一可达的空态分支：目标日落在 120 年运程之外时 `current is None`。
#: 值必须是**键名**而不是句子文本（装配走 `compose(VEDIC, opener, …)`，opener 进
#: `openers` 查文本）。真盘可达性由 golden 的 D 手钉住（T9）。
VEDIC_NONE_BRANCHES = {"dasha": "dasha_none"}

VEDIC_OPENERS = {
    "gruha_sign": "先说九曜落座这一层：九颗星各自停在哪个星座，决定了它们把你的力气往哪一处使，下面逐颗说的是你可以先认下的底色。",
    "gruha_house": "再看九曜落宫这一层：整宫制把十二个星座依次安在十二个宫位上，星落在第几宫，说的就是它在你的生活里偏向哪一块。",
    "nakshatra": "最后看星宿这一层：九曜与上升各自落在二十七宿的哪一宿，下面把这些宿的底色逐条说给你听，同一宿只讲一次。",
    "dasha": "最后看现行的大运与小运：两层主星各自带着一段时期的底色，下面把这两颗主事星各说一句，你可以对着上面的时间轴读。",
    "dasha_none": "目标日已经落在这一百二十年的运程之外，这张盘的时间轴没有当下正在走的大运与小运，这一段就没有可说的主事星，你仍可以按上面的顺序回看每一段。",
}

#: 二十七宿（T2 填）。键是宿的英文名，值是该宿的白话底色；一宿服务九曜 + 命度十行，
#: 所以条目**不点名任何曜**。
NAKSHATRA_READINGS: dict[str, str] = {}

#: 九颗主事星（T2 填）。键是曜的英文名，值是该曜主事时的白话底色；同时服务大运与小运，
#: 所以条目**不写角色词**。
DASHA_LORD_READINGS: dict[str, str] = {}

VEDIC_READINGS: dict[str, str] = {
    **vedic_plain_gruha.GRUHA_SIGN_READINGS,
    **vedic_plain_gruha.GRUHA_HOUSE_READINGS,
    **NAKSHATRA_READINGS,
    **DASHA_LORD_READINGS,
}
