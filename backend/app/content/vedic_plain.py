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
NAKSHATRA_READINGS: dict[str, str] = {
    "vedic.nakshatra.Ashwini": "阿湿毗尼这一宿带着起步与疾行的底色，事情刚有苗头你就想先动身，动作快过计划，回头再把沿途的岔路一条条收好。",
    "vedic.nakshatra.Bharani": "婆罗尼这一宿把承载与节制的分量放在一起，你愿意替别人担住一程，也清楚哪些重量不必一直留在自己身上，松手时要松得干净。",
    "vedic.nakshatra.Krittika": "基栗底伽这一宿有切割与净化的底色，你看得出一件事从哪里断开、哪里还连着，手上落下时不太留情，事后却愿意把断口收整平。",
    "vedic.nakshatra.Rohini": "楼喜尼这一宿带着生长与丰盛的底色，你做事喜欢把根扎稳再往上长，对好看与好用都有感觉，身边的人也愿意在你的照料里待着。",
    "vedic.nakshatra.Mrigashira": "弥利迦奢罗这一宿有探寻与好奇的底色，你的注意力总在找一个更合意的东西，走得不急，可一旦闻到自己想要的气味，就会一路追下去。",
    "vedic.nakshatra.Ardra": "阿陀罗这一宿把风雨与洗刷放在一起，你的心情来得猛去得也快，乱过之后反倒看得清，愿意在事情最吵的时候把话说明白。",
    "vedic.nakshatra.Punarvasu": "布纳瓦苏这一宿带着回返与复元的底色，你摔过一跤也愿意再试一次，对人对事都留着重来的余地，走过一圈往往回到最初想守的那一点。",
    "vedic.nakshatra.Pushya": "布沙这一宿有供养与守护的底色，你习惯先把身边人安顿好，再回头处理自己的事，别人托付给你的东西通常会被照看得很仔细。",
    "vedic.nakshatra.Ashlesha": "阿湿利沙这一宿带着缠绕与洞悉的底色，你看人看事容易看进细处，也懂得什么时候把话绕开，心里那条线一旦收紧就很难松开。",
    "vedic.nakshatra.Magha": "摩伽这一宿有承继与分量的底色，你对来处与旧例看得很重，做事愿意顺着老规矩的次序来，站到人前时也希望自己撑得住那份期待。",
    "vedic.nakshatra.Purva Phalguni": "前发座这一宿带着享乐与舒展的底色，你懂得在正事之间给自己留一点轻松，喜欢把日子过得好看，身边的人也常被你带得松快起来。",
    "vedic.nakshatra.Uttara Phalguni": "后发座这一宿有结伴与照拂的底色，你愿意把好处分给一起做事的人，关系一旦定下来就守得住，别人也乐意把长久的事交到你手上。",
    "vedic.nakshatra.Hasta": "哈斯塔这一宿把灵巧与手艺放在一起，你手上能做细活，脑子转得也快，一件难缠的小事到了你这里，常常三两下就被理顺。",
    "vedic.nakshatra.Chitra": "质多罗这一宿带着巧思与光彩的底色，你对样子好不好看格外在意，做东西喜欢留一处让人眼前一亮的地方，也肯为这点讲究多花功夫。",
    "vedic.nakshatra.Swati": "室伐底这一宿有独立与流动的底色，你受不住被人攥得太紧，凡事愿意自己拿主意，风向变了就顺势调一调，脚下却始终踩着自己的节奏。",
    "vedic.nakshatra.Vishakha": "毗舍佉这一宿把目标与执拗放在一起，你看准一处就不太换方向，路上分岔再多也愿意试到走通为止，只是偶尔忘了给自己留个歇脚的缝。",
    "vedic.nakshatra.Anuradha": "阿努罗陀这一宿有交情与同行的底色，你把一起走的人看得很重，愿意为了合得来的人让一步，心里却始终盼着这份情分是对等的。",
    "vedic.nakshatra.Jyeshtha": "耆宿这一宿带着优先与担当的底色，你容易被推到领头的位置，出了事先想怎么兜住，久了也要留意自己肩上的担子是不是堆得太满。",
    "vedic.nakshatra.Mula": "牟拉这一宿有挖根与拆解的底色，你不满足于表面的说法，凡事想弄明白底下那层，旧的结不解开就宁可先把它连根拔起。",
    "vedic.nakshatra.Purva Ashadha": "前阿沙荼这一宿把冲刷与宣告放在一起，你开口时不太绕弯，认定的事愿意当众说清楚，被人泼过冷水也照样把话讲完。",
    "vedic.nakshatra.Uttara Ashadha": "后阿沙荼这一宿带着耐力与定局的底色，你能在一件事上熬很久，不靠一时兴起，等到别人松手的时候，你往往还站在原地做最后一程。",
    "vedic.nakshatra.Shravana": "室罗伐那这一宿有聆听与求知的底色，你从别人的话里捡到的东西比说出口的多，愿意先听完整再开口，也容易在故事与旧闻里找到线索。",
    "vedic.nakshatra.Dhanishta": "陀尼沙这一宿带着节奏与聚拢的底色，你对步子合不合拍很敏感，做事喜欢和人对上拍子，有了余力也愿意把一群人拢在一处。",
    "vedic.nakshatra.Shatabhisha": "百药这一宿有医治与深藏的双重底色，占着这个位置时，你看得见别人身上的疼，也习惯把自己那一份收起来。",
    "vedic.nakshatra.Purva Bhadrapada": "前婆罗钵提这一宿把灼热与理想放在一起，你看事情容易看到极端的那一面，心里揣着一团想把旧东西烧掉的火，出手时不太顾旁人的眼色。",
    "vedic.nakshatra.Uttara Bhadrapada": "后婆罗钵提这一宿有沉静与慈悲的底色，你遇事习惯先沉到底把情况看清，对受苦的人天然心软，嘴上不说，替你身边人挡掉的事却不少。",
    "vedic.nakshatra.Revati": "梨婆底这一宿带着收束与护送的底色，你做事愿意把最后一段路走完，别人散场之后还会回头清点，把落在原地的人和东西都照看一遍。",
}

#: 九颗主事星（T2 填）。键是曜的英文名，值是该曜主事时的白话底色；同时服务大运与小运，
#: 所以条目**不写角色词**。四条标准件共用「主事的一段里」，其余五条换开篇，
#: 让该窗口的同主止于 4（H6 八字上限）。
DASHA_LORD_READINGS: dict[str, str] = {
    "vedic.dasha_lord.Sun": "太阳主事的一段里，你把注意力放回自己身上，愿意站出来担事，也更容易在意别人有没有把你放在眼里。",
    "vedic.dasha_lord.Moon": "太阴主事的一段里，你的心思更跟着感受走，身边人的状态容易牵动你的节奏，把休息与照顾自己的时间留出来，事情反而更顺。",
    "vedic.dasha_lord.Mars": "轮到火星把力气往前推的时候，你更容易被拦路的事点着，想当场把障碍推开，冲劲上来时也要给动作留一点收势。",
    "vedic.dasha_lord.Mercury": "水星当值的时候，你的脑子转得比平日快，话也多了起来，学新东西的胃口变大，把想法说清楚之前先在纸上过一遍会更稳妥。",
    "vedic.dasha_lord.Jupiter": "木星在场的时候，你更愿意把事情往宽处想，遇到机会愿意多走一步去试，帮别人的时候也会把自己那一份算进来。",
    "vedic.dasha_lord.Venus": "金星当值的日子里，你对好看与舒服的在意变重，关系里的温度更容易被你察觉，把日子过出一点滋味会排在前面。",
    "vedic.dasha_lord.Saturn": "土星当值的日子里，你更能坐得住，愿意把没做完的事情一项项收好，进度慢下来时不用慌，压下来的重量会换来结构上的稳。",
    "vedic.dasha_lord.Rahu": "罗睺主事的一段里，你容易被没见过的东西吸引，脚步比平时更想往外探，尝新的同时也要留意自己真正想留下的是什么。",
    "vedic.dasha_lord.Ketu": "计都主事的一段里，你更愿意往回看，把一些旧关系与旧念头慢慢放下，表面上事情没多起来，心里的位置却在腾空。",
}

VEDIC_READINGS: dict[str, str] = {
    **vedic_plain_gruha.GRUHA_SIGN_READINGS,
    **vedic_plain_gruha.GRUHA_HOUSE_READINGS,
    **NAKSHATRA_READINGS,
    **DASHA_LORD_READINGS,
}
