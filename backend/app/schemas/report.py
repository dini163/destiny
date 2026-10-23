"""付费报告产品线的一进三出：预览、完整文档、无状态订单（v2.1 §3A，snake_case 直出）。

本文件声明报告层的全部响应契约：`ReportPreview`（免费预览）、`ReportDocument`（完整报告，
含无状态订单的签名令牌）、`ReportEvidenceCard`（证据卡，PRD §3A.5 的三层内容分层）。

**订单为什么是无状态的**：后端是零数据库的纯计算 API（AGENTS.md：分层里没有存储层）。
v1 的「订单 + 签名交付链接」（PRD §3A.7）用签名令牌实现：`order_id` 是输入规范的
确定性哈希前 16 位，`token` 是服务端对 `product:order_id:created_ts` 的 HMAC 签名，
`expires_at` 限定有效期。取报告时 API 验签通过后**重新生成**同一份报告 —— 引擎是
确定性的（AGENTS.md：同一输入同一版本可复现），所以无状态、可撤销、可过期，不需要任何
存储。付费与免费试用本轮明确不做（用户审批口径），订单状态在 v1 由人工在交付流程维护。

入参不在此重复定义：三个产品各用既有系统的入参（r1=`BaziHehunRequest`、
r2=`BaziNatalRequest`、r3=`BaziTransitRequest`），报告层不重算历法，也不重定义出生参数
（AGENTS.md 第 6 条）。产品 → 入参的分发在 `api/v1/report.py` 做。
"""

from typing import Literal

from pydantic import BaseModel, Field

#: 报告产品：r1 双人关系说明书 / r2 本命使用说明书 / r3 未来12个月时间地图。
ReportProduct = Literal["r1", "r2", "r3"]

#: 章节类型：summary（一页摘要）、chapter（主体章节）、action（行动清单）、
#: evidence（证据附录）、boundary（边界声明）。序在 `content/report_templates.py` 的名册里。
SectionKind = Literal["summary", "chapter", "action", "evidence", "boundary"]

#: 证据卡置信度（PRD §3A.5 的三层）：high 盘面事实 / medium 规则解释 / low 综合建议。
EvidenceConfidence = Literal["high", "medium", "low"]


class ReportEvidenceCard(BaseModel):
    """一张证据卡：一条结论 + 它的盘面依据 + 出处 + 可推翻句。

    报告写作纪律（PRD §3A.1 原则 3）：**每条结论必须有依据**。`claim` 是给人看的结论，
    `chart_fact` 是可当场核对的盘面事实（分数、柱、命中规则），`source` 是出处（语料表名/
    模板表），`falsifier` 是「怎样会被推翻」。三者分开，不混成一句话。
    """

    claim_id: str = Field(description="章节内稳定的机器键，如 r1-conflict-01。")
    claim: str = Field(description="结论原文（给人看）。")
    chart_fact: str = Field(description="盘面依据：可核对的事实（分数/柱/命中规则）。")
    source: str = Field(description="出处：语料表名或模板表名，不写「本系统」一类空出处。")
    confidence: EvidenceConfidence = Field(
        description="high=盘面事实直接支撑；medium=规则/语料解释；low=综合建议。"
    )
    falsifier: str = Field(description="可推翻句：给出可被实际经历检验/推翻的方式。")


class ReportSection(BaseModel):
    """报告的一章：标题 + 段落 + 条目 + 该章的证据卡。

    `body` 是连续段落（每段一句到几句），`bullets` 是条目型内容（如逐月节奏、宜忌清单）。
    一页摘要章只填 `bullets`（标签在前端按模板名册渲染），主体章以 `body` 为主。
    """

    id: str = Field(description="机器名，取 `report_templates.REPORT_SECTION_NAMES` 的键。")
    title: str = Field(description="中文标题，逐字取模板表名册，不由装配器现编。")
    kind: SectionKind
    body: list[str] = Field(default_factory=list, description="连续段落。")
    bullets: list[str] = Field(default_factory=list, description="条目型内容（逐月/宜忌/行动等）。")
    evidence_cards: list[ReportEvidenceCard] = Field(
        default_factory=list, description="本章关键结论的证据卡。"
    )


class ReportPreview(BaseModel):
    """免费预览（PRD §3A.2–3A.4：摘要 + 少量结论）。

    v1 不做付费与免费试用（用户审批口径），预览只承担「先看摘要与关键结论」的展示职责，
    `notice` 逐字取模板表的 `PREVIEW_NOTICE`。
    """

    product: ReportProduct
    title: str
    tagline: str
    version: str
    generated_date: str
    input_summary: str = Field(description="脱敏输入摘要：四柱/生肖/区间，不含姓名。")
    summary: list[str] = Field(description="一页摘要的条目（标签在前端按模板名册渲染）。")
    key_points: list[str] = Field(
        min_length=2, max_length=4, description="2–4 条关键结论（预览页的「少量结论」）。"
    )
    section_count: int = Field(description="完整报告的章节数，让用户知道全文范围。")
    notice: str


class ReportDocument(BaseModel):
    """一份完整报告 + 无状态订单的交付凭据（签名链接的三要素）。

    `order_id` + `token` + `expires_at` 一起构成交付链接；API 层用
    `app.core.report_orders` 的验签函数校验后按同一输入重新生成（确定性可复现）。
    """

    order_id: str = Field(description="输入规范哈希前 16 位（十六进制），同一输入恒同。")
    product: ReportProduct
    title: str
    tagline: str
    version: str = Field(description="报告模板版本，逐字取 `report_templates.REPORT_VERSION`。")
    generated_date: str = Field(description="生成日期（ISO），取服务器当日。")
    input_summary: str
    sections: list[ReportSection] = Field(description="按模板名册序排布的全部章节。")
    boundary: str = Field(description="边界声明全文，逐字取模板表（同时住在 boundary 章）。")
    token: str = Field(description="HMAC 签名令牌：`product:order_id:created_ts` 的签名。")
    expires_at: str = Field(description="链接过期时间（ISO）。")
