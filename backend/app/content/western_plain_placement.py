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

#: T1 落地 `planet_sign` 的 Sun/Moon/Mercury 三族 36 条（本族 120 条的前三族），
#: `planet_house` 一族归 T4-T6，其余各族见各批。
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
}
