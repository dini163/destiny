"""西洋本命：十颗星落十二座（120）与落十二宫（120）的白话判语表。

键由 `western_plain` 的构造器拼，所以本文件只有句子，没有键式。两族在 T1-T6 分五批填入，
已落地的行一字不改（改一行就等于改动别批已评审过的内容，那要走裁定）。

**导入次序的陷阱**：本文件引 `western_plain` 的构造器，而 `western_plain` 的聚合面又引本
文件，两模块构成刻意的环。CPython 下唯一可行的入口是先 import `western_plain`（它的构造器
定义在前、引本表在后），所有消费方（`engines/plain_corpora.py` 的 content import 段与
`tests/content/test_western_plain_corpus.py`）都照这个次序进入；先 import 本文件会让聚合面
读到半初始化表而 `AttributeError`。复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "from app.content import western_plain, western_plain_placement; print(len(western_plain.WESTERN_READINGS))"`。
"""

from app.content.western_plain import planet_house_key, planet_sign_key

#: 本表按批追加，各族当前条数不住在这里，由
#: `tests/content/test_western_plain_corpus.py::ROSTER_TARGETS` 逐批钉住（复测：
#: `cd backend && grep -n "ROSTER_TARGETS" -A8 tests/content/test_western_plain_corpus.py`）。
#: `planet_sign` 120 条归 T1-T3，`planet_house` 120 条归 T4-T6。
WESTERN_PLACEMENT_READINGS: dict[str, str] = {
    # Sun 太阳落十二座（12 条）
    planet_sign_key("Sun", "Aries"): "你太阳落在白羊，自我表达默认是抢先一步的那档，事情还没谈完就已经动手，别人读到的你是快、直、不太等人。",
    planet_sign_key("Sun", "Taurus"): "你太阳落在金牛，自我这件事要落地才踏实，把日子过成可摸到的形状比说清楚更重要，慢是稳定而不是障碍。",
    planet_sign_key("Sun", "Gemini"): "你太阳落在双子，先把事情说清楚才认得自己，兴趣多、入口快，同一时间接两三条线也不觉得拥挤。",
    planet_sign_key("Sun", "Cancer"): "你太阳落在巨蟹，自我是围着那几段亲近关系长出来的，环境软下来你才亮，被人指着依靠的那件事就是你给自己的确认。",
    planet_sign_key("Sun", "Leo"): "你太阳落在狮子，存在感要被人看见才完整，愿意给也愿意被接住，被忽略比失败更让你难受。",
    planet_sign_key("Sun", "Virgo"): "你太阳落在处女，自我认同建立在把事情做对做细上，对不对得着自己心里有杆秤，含糊和潦草最消耗你的兴致。",
    planet_sign_key("Sun", "Libra"): "你太阳落在天秤，自我的分量是在与别人的对照里称出来的，你习惯先看清双方再表态，把关系理顺就是你确认自己的方式。",
    planet_sign_key("Sun", "Scorpio"): "你太阳落在天蝎，自我表达带着不留情面的深劲，认定了就整颗心放进去，没意思就干脆收拢，表面平静底下从不肯松着。",
    planet_sign_key("Sun", "Sagittarius"): "你太阳落在射手，自我是靠一个更远的目标撑起来的，话说得直，兴趣来得快，被框在原地比吃苦更让你憋闷。",
    planet_sign_key("Sun", "Capricorn"): "你太阳落在摩羯，自我感靠扛住一件件难事攒出来，你不怕慢，怕的是手里的事没分量，被交给的责任越重你越站得稳。",
    planet_sign_key("Sun", "Aquarius"): "你太阳落在水瓶，自我是带着距离看的，先站到人群外面把局面看全，再决定靠近与否，独特对你而言不是姿态而是呼吸。",
    planet_sign_key("Sun", "Pisces"): "你太阳落在双鱼，自我表达是水一样漫开的，不设硬边界，先感受再理解，能把含糊的东西化成体恤，也容易被人家的气氛带着走。",
    # Moon 月亮落十二座（12 条）
    planet_sign_key("Moon", "Aries"): "你月亮落在白羊，情绪来得快去得也快，火发完就翻篇，你不擅长把不满攒在心里，当下那一阵就是全部。",
    planet_sign_key("Moon", "Taurus"): "你月亮落在金牛，安稳感来得很慢也很实在，一张床、一顿饭、一段不着急的时间，比任何解释都能让你松下来。",
    planet_sign_key("Moon", "Gemini"): "你月亮落在双子，心情要靠说出来才理顺，同时装着好几种情绪也不觉得挤，闷住的安静反而让你发慌。",
    planet_sign_key("Moon", "Cancer"): "你月亮落在巨蟹，安全感排在最前面，屋里气氛一凉你最先察觉，被护着的时候软，觉出不对就先缩回自己的壳。",
    planet_sign_key("Moon", "Leo"): "你月亮落在狮子，情绪要被人接住也要被人看见，夸到点上你整个人都亮起来，被当众冷落是那种关不上的疼。",
    planet_sign_key("Moon", "Virgo"): "你月亮落在处女，安定感来自把事情理出条理，情绪也要有出处，说不清来由的那一部分最让你不安。",
    planet_sign_key("Moon", "Libra"): "你月亮落在天秤，情绪要放得下靠的是一段说得通的关系，有人肯和你商量你就稳，独自僵持的拉锯最磨人也最耗你。",
    planet_sign_key("Moon", "Scorpio"): "你月亮落在天蝎，感受力深而不留缝，喜欢与不喜欢都沉在底下一层，表面过得平静，内里那本账从来没有翻篇。",
    planet_sign_key("Moon", "Sagittarius"): "你月亮落在射手，心气要靠往前走恢复，换个地方换一句话说，情绪就松开，困在原地反复咀嚼最伤你。",
    planet_sign_key("Moon", "Capricorn"): "你月亮落在摩羯，情绪收得住也扛得起，你习惯把不安换成手上正在做的事，人前不露，人后自己慢慢化开。",
    planet_sign_key("Moon", "Aquarius"): "你月亮落在水瓶，情绪要放到一个没人看见的地方处理，越乱越想抽身冷静，被过度贴近反而让你往后缩。",
    planet_sign_key("Moon", "Pisces"): "你月亮落在双鱼，感受没有硬边，旁人的低气压也会漫进你这里，安静下来才能把湿透的部分晾干，硬撑最耗你。",
    # Mercury 水星落十二座（12 条）
    planet_sign_key("Mercury", "Aries"): "你水星落在白羊，思考是靠先动起来铺路的，想到就开口，语速直，争论里你看重把话打到点上多过周全。",
    planet_sign_key("Mercury", "Taurus"): "你水星落在金牛，说出来的话要落地有声，你不着急改口，想得慢而稳，一句是一句，含糊其辞不是你的风格。",
    planet_sign_key("Mercury", "Gemini"): "你水星落在双子，这是它最顺的一格，话说得快也接得快，几条线并行不打结，把事情解释清楚本身就是乐趣。",
    planet_sign_key("Mercury", "Cancer"): "你水星落在巨蟹，思维带着体温，先感受再推理，心里有过的事会顺着感觉说成道理，光凭冷数据说服不了你。",
    planet_sign_key("Mercury", "Leo"): "你水星落在狮子，表达有感染力也爱把话讲得响亮，你肯为观点站台，被反驳时先热后冷，气势比修辞更足。",
    planet_sign_key("Mercury", "Virgo"): "你水星落在处女，分析是它的看家本事，分辨细微差别，挑出说法里站不住的那一处，话说得准比说得漂亮更要紧。",
    planet_sign_key("Mercury", "Libra"): "你水星落在天秤，思考的秤两头都要摆一摆，你习惯先听完两边再下判断，说理讲体面，硬碰硬的场合会让你收声。",
    planet_sign_key("Mercury", "Scorpio"): "你水星落在天蝎，想事情往深处钻，表面话瞒不过你，开口短而准，不轻易说，一说就奔着要害去。",
    planet_sign_key("Mercury", "Sagittarius"): "你水星落在射手，思路大而不绕，先抓大方向再补细节，话直得容易撞人，也乐意给远处的可能性留着位置。",
    planet_sign_key("Mercury", "Capricorn"): "你水星落在摩羯，思考像砌墙，一句一句往实处码，说出口的都打算兑现，空谈在你这里过不了自己那一关。",
    planet_sign_key("Mercury", "Aquarius"): "你水星落在水瓶，思路自带旁观视角，先把事拆成结构再说话，点子怪但讲得通，越不寻常的联结越合你胃口。",
    planet_sign_key("Mercury", "Pisces"): "你水星落在双鱼，想事情带画面和联想，逻辑排在第二层，意象先到，说得别人发愣的时候自己已经绕完了一圈。",
    # Venus 金星落十二座（12 条）
    planet_sign_key("Venus", "Aries"): "你金星落在白羊，喜欢这件事来得快而且明晃晃，先有心跳再有了解，好感摆在脸上，藏不住也懒得藏，淡下去的时候同样干脆。",
    planet_sign_key("Venus", "Taurus"): "你金星落在金牛，喜欢要落到摸得到的东西上，一顿好饭、一段不着急的相处，安稳比新鲜更要紧，换人容易换习惯难。",
    planet_sign_key("Venus", "Gemini"): "你金星落在双子，先聊得来才有后面的事，好奇一张说得清楚的嘴，同时接几种好感也不觉得乱，注意力来得快，走得也快。",
    planet_sign_key("Venus", "Cancer"): "你金星落在巨蟹，喜欢里带着照顾，先觉得安全才敢靠近，对方说过的小事都放在心上，被小心对待的时候最动心，气氛一冷就先把自己收回去。",
    planet_sign_key("Venus", "Leo"): "你金星落在狮子，喜欢要大大方方被人看见，肯给也肯收下，被郑重对待就觉得一切都值，热情是有来有往的那一份体面。",
    planet_sign_key("Venus", "Virgo"): "你金星落在处女，好感是靠细节一点点攒起来的，把该做的做到位比讲漂亮话更动人，不轻易出口，一说就是替人把手边的事理顺。",
    planet_sign_key("Venus", "Libra"): "你金星落在天秤，喜欢这件事要先有对等才安心，你在意的是两个人之间那种来回的分寸，而不是单方面给得多。",
    planet_sign_key("Venus", "Scorpio"): "你金星落在天蝎，喜欢是整颗心压下去的那种浓度，要么全给要么不给，试探两句就看得出真不真，淡不下去，也不肯只淡着。",
    planet_sign_key("Venus", "Sagittarius"): "你金星落在射手，喜欢要带着余地才好呼吸，玩得到一起比什么都要紧，话说得直也不往心里搁，路走得远的时候这份心气反而更热。",
    planet_sign_key("Venus", "Capricorn"): "你金星落在摩羯，喜欢要经得起时间和现实两头称，不轻易表态，认了之后也不常说，把日子一天天过稳就是这一格表达温度的方式。",
    planet_sign_key("Venus", "Aquarius"): "你金星落在水瓶，喜欢里先给各自留着自由，说得来比黏得住更有吸引力，用一种旁观的诚实去对人，靠得太近反而把温度弄丢。",
    planet_sign_key("Venus", "Pisces"): "你金星落在双鱼，喜欢是带着体谅的，先替对方找出理由，边界容易让出去，付出不计数，被提醒的时候才想到自己也有一份。",
    # Mars 火星落十二座（12 条）
    planet_sign_key("Mars", "Aries"): "你火星落在白羊，使力的方式是立刻冲上去，冲突当场就反应完，不记仇也不拖延，这股劲快，同时也直接。",
    planet_sign_key("Mars", "Taurus"): "你火星落在金牛，发力慢而持久，不轻易启动，认定了就一步不挪，力气全花在把东西真正做完上，僵持最能见出你的耐性。",
    planet_sign_key("Mars", "Gemini"): "你火星落在双子，使力靠嘴也靠信息，把话讲透就算推进，同时开几条线也不觉得累，力气容易铺得太散，收拢一处才算到位。",
    planet_sign_key("Mars", "Cancer"): "你火星落在巨蟹，动手之前先护住自己人，劲是带着情绪使的，心里有底才肯往前，被碰到在意的那几段关系时最快，过后又容易收回。",
    planet_sign_key("Mars", "Leo"): "你火星落在狮子，出力要出得漂亮，被认可就是燃料，站到人前便把那口气撑住，面子上这一步不肯让，热劲来得足，走得也明。",
    planet_sign_key("Mars", "Virgo"): "你火星落在处女，力气花在把事做对上，一处一处修到能用为止，动手前先把步骤排好，冲劲不显，却在细节上最舍得耗。",
    planet_sign_key("Mars", "Libra"): "你火星落在天秤，动手前要把两边的道理都摆平，正面冲撞会让你先退一步，力气多用在把话讲通上，真急了反倒说不出重话。",
    planet_sign_key("Mars", "Scorpio"): "你火星落在天蝎，劲沉在底下一点点攒，动起来就不留余地，盯住的事不撒手，别人看不出的那一份持久，才是这股劲真正的去处。",
    planet_sign_key("Mars", "Sagittarius"): "你火星落在射手，使力朝着一个方向一路往前推，目标越大越来劲，细节上肯省，热情上肯花，被按在原地反复磨最耗这股劲。",
    planet_sign_key("Mars", "Capricorn"): "你火星落在摩羯，力气是用来把事做成的，讲效率也讲分寸，不到要动的时候不动，一动就奔着结果去，最烦白费的那一份力。",
    planet_sign_key("Mars", "Aquarius"): "你火星落在水瓶，出力出在意想不到的地方，先把事拆成一套做法再动手，为道理不为面子，越是要人随大流的场合越想按自己的方式来。",
    planet_sign_key("Mars", "Pisces"): "你火星落在双鱼，使力的方式是绕着走，不正面顶，靠耐心和软磨把事挪开，气氛不对就先退，劲用在体察上多过用在推进上。",
    # Jupiter 木星落十二座（12 条）
    planet_sign_key("Jupiter", "Aries"): "你木星落在白羊，运气在抢先开局那一段，越是靠勇气的事越容易顺，一路直冲的劲头反倒替你开出方向，慢下来时势就先散。",
    planet_sign_key("Jupiter", "Taurus"): "你木星落在金牛，扩张走在实处，一样样攒在手边的东西才让人安心，机会来得慢而稳，肯在吃穿用度上花心思，日子也就过得厚。",
    planet_sign_key("Jupiter", "Gemini"): "你木星落在双子，运气藏在听来的消息里，多认识几个人就多一条路，学什么都上手快，长处是把几种说法接成自己能用的部分。",
    planet_sign_key("Jupiter", "Cancer"): "你木星落在巨蟹，被托住的感觉来自那几段亲近关系，屋里气氛一好整个人都放开，肯给自家人留余地，好运常常和照顾别人一起来。",
    planet_sign_key("Jupiter", "Leo"): "你木星落在狮子，运气在人前展开，被人看见的时候机会容易凑到跟前，肯大方给也肯被夸，舞台感一丢，气势先矮下去一截。",
    planet_sign_key("Jupiter", "Virgo"): "你木星落在处女，扩张走在一件件小事里，把手艺磨精就是这一格的运气路，讲用处不讲排场，长处是把乱的东西理成能跑的秩序。",
    planet_sign_key("Jupiter", "Libra"): "你木星落在天秤，运气在谈得成的场合里，讲公道话容易引来帮手，两头的道理都肯听，机会多在与人商量处出现，独断反倒把局收窄。",
    planet_sign_key("Jupiter", "Scorpio"): "你木星落在天蝎，扩张走深不走宽，越是难啃的事越给你长劲，看穿一层就敢往一层里去，运气带着烈度，来得慢但一次给得足。",
    planet_sign_key("Jupiter", "Sagittarius"): "你木星落在射手，运气与扩张都走在远的方向，路走得越开、见的事越多，你越容易觉得自己被托住。",
    planet_sign_key("Jupiter", "Capricorn"): "你木星落在摩羯，运气靠一格格往上垒，肯多担一点就多接一分分量，扩得慢却扎实，时间在这条路上是站在你这一边的。",
    planet_sign_key("Jupiter", "Aquarius"): "你木星落在水瓶，运气在人群和新鲜念头里，圈子里多认识一位就多开一扇窗，肯给不相干的人留余地，扩张的方向是先人后己。",
    planet_sign_key("Jupiter", "Pisces"): "你木星落在双鱼，扩张走的不是数得清的路子，靠感受和想象把世界放大，对谁都不忍把话说死，运气来得含糊，常在你不追着要结果的时候出现。",
}
