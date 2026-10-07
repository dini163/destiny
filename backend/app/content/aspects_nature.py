"""相位属性表：五类主要相位 → （性质键，中文档名）（戊组 spec §5.2 裁定 R49）。

这张表原本以 `_NATURE` 之名住在两个引擎里、各一份逐字复制。搬成 content 表的理由不是
「两处重复不美」这一条美学，而是**出处诚实性**：`provenance.tables` 的规矩是「读了哪张表
就列哪张，宁缺勿多」（AGENTS §7），而一张住在引擎里的 dict 无法登记进 `*_CONTENT_SOURCES`，
于是行运与合盘两页永远少列一张它们真读了的表。

三档分类（合相=融合、六合与拱=和谐、刑与冲=挑战）是西洋占星的**通行归类**，不是平台自撰的
判语，也不是古籍引文——所以出处串自述的是「平台整理的通行分类」，不署任何书名。
`tests/content/test_aspects_nature.py` 的第二条测钉住「两个引擎都改引本表、都不再自带副本」，
这条是搬家唯一的验收。
"""

ASPECT_NATURE_SOURCE = (
    "平台整理的相位属性表，按西洋占星通行的三档分类标注五类主要相位的性质，"
    "供行运与合盘两个引擎逐条引用。不是古籍引文，不署任何书名，不构成医疗、法律、财务建议。"
)

ASPECT_NATURE: dict[str, tuple[str, str]] = {
    "conjunction": ("fusion", "融合"),
    "sextile": ("harmonious", "和谐"),
    "trine": ("harmonious", "和谐"),
    "square": ("challenging", "挑战"),
    "opposition": ("challenging", "挑战"),
}
