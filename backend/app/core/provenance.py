"""出处措辞：一句在响应、语料表与账本行之间必须逐字一致的说明。

放在 `core/` 而不是 `content/` 或 `schemas/`，是因为它的读者横跨三层（AGENTS.md 第 1 条
的分层方向）：语料表拿它拼书级出处，`schemas/scoring.py` 拿它作账本行的默认出处，引擎拿它
填 `ScoreFactor.source`。原先它住在 `schemas/scoring.py`，于是三处 `content/` 反向 import
`schemas/` —— 违反分层方向的偏偏是一句措辞而不是数据契约，这就是它搬家的全部理由。
"""

#: The one wording used when a figure comes from this system's own weighting
#: instead of a classic. Defined once so no module paraphrases it differently.
MODEL_PARAM_SOURCE = "模型参数（本系统加权，非古籍赋分）"
