"""西洋本命：十颗星之间 225 条主要相位的白话判语表（T10-T14 按相位类型五批填入）。

键由 `western_plain.aspect_key` 拼，所以本文件只有句子，没有键式；本批 T10 起填合相 45 条，
六合/刑相/拱相/冲相归 T11-T14。

**导入次序的陷阱**：本文件与 `western_plain_placement` 一样要引 `western_plain` 的构造器，
而 `western_plain` 的聚合面又在本模块底部引回来，两模块构成刻意的环。CPython 下唯一可行的
入口是先 import `western_plain`（构造器定义在前、引分表在后），所有消费方
（`engines/plain_corpora.py` 的 content import 段与 `tests/content/test_western_plain_corpus.py`）
都照这个次序进入；先 import 本文件会让聚合面读到半初始化表而 `AttributeError`。
复测：`cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -c "import app.content.western_plain_aspect"` 红（预期），
`... -c "from app.content.western_plain import WESTERN_READINGS; print(len(WESTERN_READINGS))"` 绿。
"""

from app.content.western_plain import aspect_key

WESTERN_ASPECT_READINGS: dict[str, str] = {
    # 合相（45 条，键序 = `combinations(PLANETS, 2)` = G32 的合法序）
    aspect_key("Sun", "Moon", "conjunction"): "你盘上太阳与月亮成合相，想要的和感觉到的基本朝同一个方向，内在拉扯少，代价是不容易站到另一个角度看自己。",
    aspect_key("Sun", "Mercury", "conjunction"): "你盘上太阳与水星成合相，想明白和说出口共用一条道，主意没落定话已经成形，里外之间没有中转，第二套讲法便没处落脚。",
    aspect_key("Sun", "Venus", "conjunction"): "你盘上太阳与金星成合相，看上的和愿意担的出自同一处，人走到哪一路，热便带到哪一路，亮处没有反面，不容易觉出自己也有不想动心的那头。",
    aspect_key("Sun", "Mars", "conjunction"): "你盘上太阳与火星成合相，想做的和动手做的中间没有传话的人，起手自带全股力气，不藏进度也不留后手，歇下来时找不出一个不费力的说法。",
    aspect_key("Sun", "Jupiter", "conjunction"): "你盘上太阳与木星成合相，认的方向会自行放大，一份心意顺手多铺一层，热起来连着身边几处一同亮，落空时也整片跟着凉，没有单独收着这一步。",
    aspect_key("Sun", "Saturn", "conjunction"): "你盘上太阳与土星成合相，往前的力和肩上的担子拧成一股，起手便压着分量，稳住之后觉出踏实，轻的一面从不外摆。",
    aspect_key("Sun", "Uranus", "conjunction"): "你盘上太阳与天王星成合相，你是谁和你想推翻的东西捆在一处，路子换得越快越像回到原位，新的一套还没摆稳，旧的已经先被拆掉。",
    aspect_key("Sun", "Neptune", "conjunction"): "你盘上太阳与海王星成合相，认定的朝向和一层雾气同来，亮光先照到想象那头，落到实处的部分还得回头找第二遍，说不清哪一段来自眼前。",
    aspect_key("Sun", "Pluto", "conjunction"): "你盘上太阳与冥王星成合相，整股力气并成一个朝向，一出手就要见底，退回来也不留一半，全力只喂得饱一处，别处一直空着。",
    aspect_key("Moon", "Mercury", "conjunction"): "你盘上月亮与水星成合相，心情和说法共用一张嘴，顺的时候整套讲清楚，堵的时候连自己也听不出歪在第几层，情绪很少有单独搁着的时候。",
    aspect_key("Moon", "Venus", "conjunction"): "你盘上月亮与金星成合相，安心感和心动的来处挨在一起，一处暖起来几处都跟着顺，凉掉的一头不肯单独立着，判断总带当下的温度。",
    aspect_key("Moon", "Mars", "conjunction"): "你盘上月亮与火星成合相，火气跟着心情走，护人的念头来得比解释快，力道放出去时心里已经软了半截，收不干净就转去磨手边的事。",
    aspect_key("Moon", "Jupiter", "conjunction"): "你盘上月亮与木星成合相，心气一放开就跟着宽一片，好的时候愿意多给一层，情绪来得厚去得慢，没人可给的那几天，这份热只能往回收。",
    aspect_key("Moon", "Saturn", "conjunction"): "你盘上月亮与土星成合相，安稳感起初就压着称量，后果量过了才松一口气，情绪不往明处放，日子久了反倒练出耐性，只是那份心事说得晚。",
    aspect_key("Moon", "Uranus", "conjunction"): "你盘上月亮与天王星成合相，心情说换便换，亲近里始终留一块没人知道的位置，抽身去冷静这一手很自然，软下来之后总要独自待一阵。",
    aspect_key("Moon", "Neptune", "conjunction"): "你盘上月亮与海王星成合相，感受和外头的界线偏软，沉下来的气压容易漫进来，安抚顺手让到末位，独处一阵才认出刚才接住的并不全是你的。",
    aspect_key("Moon", "Pluto", "conjunction"): "你盘上月亮与冥王星成合相，情绪从头到尾整份给出，一半也不留在外头，软下来要很长的回收，浓度摆不到明处，讲出口反而变轻。",
    aspect_key("Mercury", "Venus", "conjunction"): "你盘上水星与金星成合相，讲得顺和入耳的点落在同一处，话里带温度，选词时已经先照顾气氛，硬道理那一段总绕得漂亮了些。",
    aspect_key("Mercury", "Mars", "conjunction"): "你盘上水星与火星成合相，念头一出口力气也跟上，两边同时开动，收话比起手慢了半拍，话赶在前头，后面的分量反倒追不上。",
    aspect_key("Mercury", "Jupiter", "conjunction"): "你盘上水星与木星成合相，一条想法接一条说法往外铺，听来的道理很快变成成套讲法，问起来的兴致没有尽头，几条线索同时开着，收束那步总排在末尾。",
    aspect_key("Mercury", "Saturn", "conjunction"): "你盘上水星与土星成合相，开口之前你习惯先上一遍秤，说得慢而准，一套说法回头再核也不改口，临时接话时容易错过前半句。",
    aspect_key("Mercury", "Uranus", "conjunction"): "你盘上水星与天王星成合相，念头转得快也拐得急，话到中段岔进新的支路，前后在你看来连成一串，外头听着却像断开在两处。",
    aspect_key("Mercury", "Neptune", "conjunction"): "你盘上水星与海王星成合相，讲出的句子自带画面，逻辑走不通便靠联想补，说法因此动人，补上去的是哪一层，事后再看才显出来。",
    aspect_key("Mercury", "Pluto", "conjunction"): "你盘上水星与冥王星成合相，一个问题从头问到根，浮面的说法过不了这一关，追到底才肯停，话太用力，轻一点的场合接不住。",
    aspect_key("Venus", "Mars", "conjunction"): "你盘上金星与火星成合相，心动和出手是同一股力气，喜欢就整个人往前，热烈里带着急，凉得也快，中间没有缓冲的余地。",
    aspect_key("Venus", "Jupiter", "conjunction"): "你盘上金星与木星成合相，喜好一路放宽，好的体验总想再多要一层，热的时候铺开一大片，把慷慨当成日常，收不住时格外伤。",
    aspect_key("Venus", "Saturn", "conjunction"): "你盘上金星与土星成合相，好感先过一道现实的秤才肯落地，慢而结实，认下的一段能续很多年，没定的一程从不对外说。",
    aspect_key("Venus", "Uranus", "conjunction"): "你盘上金星与天王星成合相，亲近和各自的空间并排摆着，黏不住的时候不是变淡，是换了相处法，坦率看起来反倒像疏远。",
    aspect_key("Venus", "Neptune", "conjunction"): "你盘上金星与海王星成合相，看上的先在心里描一层软光，体贴和想象绕成圈，分不出是心动还是愿意信，真人反倒站在描好的光后面。",
    aspect_key("Venus", "Pluto", "conjunction"): "你盘上金星与冥王星成合相，好感一上来朝深处去，给的是整份，浅一层的情分留不住，认真到不留退路，松开来攒得很慢。",
    aspect_key("Mars", "Jupiter", "conjunction"): "你盘上火星与木星成合相，使出去的力气自带扩的势头，一热便整片摊开，越连着做越有兴头，收口那段最不顺手，摊开的多，落定的少。",
    aspect_key("Mars", "Saturn", "conjunction"): "你盘上火星与土星成合相，出力与压着的力气拧成一束，起手沉，中段稳，跑长路比冲刺更像你，耐性是一段段磨出来的，急反而见不出用处。",
    aspect_key("Mars", "Uranus", "conjunction"): "你盘上火星与天王星成合相，动手的节奏说不准，忽然一阵紧，忽然改一套做法，快起来不受旁的安排管，做到第二遍便提不起兴致。",
    aspect_key("Mars", "Neptune", "conjunction"): "你盘上火星与海王星成合相，出力的朝向跟着感觉走，兴致在便整股压上，兴致不在连起手都找不着由头，力气很难按时段放出来。",
    aspect_key("Mars", "Pluto", "conjunction"): "你盘上火星与冥王星成合相，力气一路攒满才肯放出去，一投就想到底，中途收手这一招用不来，没有小用法的档位，平常小事也当成大事使。",
    aspect_key("Jupiter", "Saturn", "conjunction"): "你盘上木星与土星成合相，扩出去和收回来走的是同一段路，热劲带着秤，越铺越要落地，长进慢而沉，两头都想顾的时候最易迟疑。",
    aspect_key("Jupiter", "Uranus", "conjunction"): "你盘上木星与天王星成合相，扩开的方向说变便变，一套想法还没用熟就被新的顶掉，来得急去得也急，很少有哪条路走到底，力气分在好几处。",
    aspect_key("Jupiter", "Neptune", "conjunction"): "你盘上木星与海王星成合相，放大这件事没有边，想象一层压一层往前推，宽景铺得很远，里头没有一格是量过的，收拢的功夫排在很后。",
    aspect_key("Jupiter", "Pluto", "conjunction"): "你盘上木星与冥王星成合相，力气带着浓度，起头便奔最深的一层，扩开的不是排场而是底下一整层，投入没有中档，要么满要么收。",
    aspect_key("Saturn", "Uranus", "conjunction"): "你盘上土星与天王星成合相，守旧的力与想改的力同在一处，一手压住分量，一手挪开成规，慢而稳，两桩事从不排队，同时压着。",
    aspect_key("Saturn", "Neptune", "conjunction"): "你盘上土星与海王星成合相，担子底下垫着一层想象，认真与模糊同时在场，局面稳住之后有空辨认那层雾，这份辨认常常拖很久。",
    aspect_key("Saturn", "Pluto", "conjunction"): "你盘上土星与冥王星成合相，承担的力一路朝里压，扛住的重量不显在外，放下来得靠长年磨，耐力很少分给别处，整年压在同一副担子上。",
    aspect_key("Uranus", "Neptune", "conjunction"): "你盘上天王星与海王星成合相，跳脱与弥散合流，一边拆手上的规矩，一边补眼前景象，怪处自有它的秩序，中间几步最难摆到话里。",
    aspect_key("Uranus", "Pluto", "conjunction"): "你盘上天王星与冥王星成合相，改的主意连着底下的力，动了就不肯留半分，换过几轮根子没变，改到一半就想改到底，过渡那段不太肯走。",
    aspect_key("Neptune", "Pluto", "conjunction"): "你盘上海王星与冥王星成合相，柔软和深沉拧在一处，想象往底下去，感受往开里铺，真假之间最难分，许多年以后才看清当时添上的是什么。",
}
