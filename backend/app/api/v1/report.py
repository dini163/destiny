"""付费报告产品线 HTTP 适配器（v2.1 §3A，薄层：分发入参 + 验签交付）。

端点按产品分派到既有系统的入参 schema（r1=合婚 / r2=本命 / r3=岁运），装配全部交给
`engines/report_composer.py`。v1 不做付费与免费试用：`preview` 给免费摘要，
`generate` 直接产出完整报告 + 签名链接（订单状态由人工交付流程维护），
`fetch` 验签通过后按同一输入重算 —— 无状态、可撤销、可过期。

验签失败统一 404：不区分「伪造」与「过期」（调用方不需要知道），前端已有 404 兜底文案。
"""

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.core.report_orders import derive_order_id, verify_token
from app.engines.report_composer import compose_preview, compose_report
from app.schemas.bazi import BaziNatalRequest
from app.schemas.bazi_hehun import BaziHehunRequest
from app.schemas.bazi_transit import BaziTransitRequest
from app.schemas.report import (
    ReportDocument,
    ReportPreview,
    ReportProduct,
)

router = APIRouter(prefix="/report")


@router.post("/r1/preview", response_model=ReportPreview, summary="R1 双人关系说明书 · 免费预览")
async def report_r1_preview(request: BaziHehunRequest) -> ReportPreview:
    """合婚输入的免费预览：一页摘要 + 少量结论（PRD §3A.2）。"""
    return compose_preview("r1", request, reference_date=request.reference_date)


@router.post("/r1/generate", response_model=ReportDocument, summary="R1 双人关系说明书 · 生成完整报告")
async def report_r1_generate(request: BaziHehunRequest) -> ReportDocument:
    """生成完整《双人关系说明书》+ 签名交付链接（v1 人工交付，不接支付）。"""
    return compose_report("r1", request, reference_date=request.reference_date)


@router.post("/r2/preview", response_model=ReportPreview, summary="R2 本命使用说明书 · 免费预览")
async def report_r2_preview(request: BaziNatalRequest) -> ReportPreview:
    """本命输入的免费预览：一页摘要 + 1–2 条关键结论（PRD §3A.3）。"""
    return compose_preview("r2", request, reference_date=request.reference_date)


@router.post("/r2/generate", response_model=ReportDocument, summary="R2 本命使用说明书 · 生成完整报告")
async def report_r2_generate(request: BaziNatalRequest) -> ReportDocument:
    """生成完整《本命使用说明书》+ 签名交付链接。"""
    return compose_report("r2", request, reference_date=request.reference_date)


@router.post("/r3/preview", response_model=ReportPreview, summary="R3 未来12个月时间地图 · 免费预览")
async def report_r3_preview(request: BaziTransitRequest) -> ReportPreview:
    """岁运输入的免费预览：年度主题 + 高杠杆/低能量窗口（PRD §3A.4）。"""
    return compose_preview("r3", request, reference_date=request.reference_date)


@router.post("/r3/generate", response_model=ReportDocument, summary="R3 未来12个月时间地图 · 生成完整报告")
async def report_r3_generate(request: BaziTransitRequest) -> ReportDocument:
    """生成完整《未来12个月时间地图》+ 签名交付链接。"""
    return compose_report("r3", request, reference_date=request.reference_date)


def _verify_and_compose(product: ReportProduct, order_id: str, token: str, request) -> ReportDocument:
    """验签 + 校验输入与订单匹配后重算报告（三个 fetch 端点共用的同一段判断）。

    v1 无存储（后端零数据库），「链接」= 订单号 + 签名令牌 + 输入（输入由前端本地暂存，
    人工交付时随链接一并说明）。`order_id` 必须与本次输入的规范哈希一致，否则视为
    链接与输入不匹配。Phase 2 引入输入暂存后本端点契约不变，只是不再要求请求体。
    """
    settings = get_settings()
    if not verify_token(
        settings.report_secret, product, order_id, token, settings.report_link_ttl_hours
    ):
        raise HTTPException(status_code=404, detail="report link invalid or expired")
    if derive_order_id(product, request) != order_id:
        raise HTTPException(status_code=404, detail="report order does not match input")
    return compose_report(product, request, reference_date=getattr(request, "reference_date", None))


@router.post("/r1/{order_id}", response_model=ReportDocument, summary="凭 R1 签名链接取回报告")
async def report_fetch_r1(order_id: str, token: str, request: BaziHehunRequest) -> ReportDocument:
    return _verify_and_compose("r1", order_id, token, request)


@router.post("/r2/{order_id}", response_model=ReportDocument, summary="凭 R2 签名链接取回报告")
async def report_fetch_r2(order_id: str, token: str, request: BaziNatalRequest) -> ReportDocument:
    return _verify_and_compose("r2", order_id, token, request)


@router.post("/r3/{order_id}", response_model=ReportDocument, summary="凭 R3 签名链接取回报告")
async def report_fetch_r3(order_id: str, token: str, request: BaziTransitRequest) -> ReportDocument:
    return _verify_and_compose("r3", order_id, token, request)
