"""Report previews, internal generation and manually authorised snapshot delivery.

Production forbids self-service personal generation. Public fixed samples carry
no delivery credential. Snapshot retrieval uses a bearer token in the body,
while legacy recomputation remains development-only.
"""

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import get_settings
from app.core.errors import ReportDeliveryError
from app.core.report_access import require_operator, require_self_service
from app.core.report_orders import derive_order_id, verify_token
from app.core.report_store import load_delivery, revoke_delivery, save_delivery
from app.engines.report_composer import compose_preview, compose_report
from app.schemas.bazi import BaziNatalRequest
from app.schemas.bazi_hehun import BaziHehunRequest
from app.schemas.report import (
    DeliveryLookup,
    ReportDocument,
    ReportPreview,
    ReportProduct,
    ReportRelationshipRequest,
    ReportTimeRequest,
)

router = APIRouter(prefix="/report")


@router.post("/r1/preview", response_model=ReportPreview, summary="R1 双人关系说明书 · 免费预览")
async def report_r1_preview(request: ReportRelationshipRequest) -> ReportPreview:
    """合婚输入的免费预览：一页摘要 + 少量结论（PRD §3A.2）。"""
    return compose_preview("r1", request, reference_date=request.reference_date)


@router.post(
    "/r1/generate", response_model=ReportDocument, summary="R1 双人关系说明书 · 生成完整报告"
)
async def report_r1_generate(request: ReportRelationshipRequest) -> ReportDocument:
    """生成完整《双人关系说明书》+ 签名交付链接（v1 人工交付，不接支付）。"""
    require_self_service()
    return compose_report("r1", request, reference_date=request.reference_date)


@router.post("/r2/preview", response_model=ReportPreview, summary="R2 本命使用说明书 · 免费预览")
async def report_r2_preview(request: BaziNatalRequest) -> ReportPreview:
    """本命输入的免费预览：一页摘要 + 1–2 条关键结论（PRD §3A.3）。"""
    return compose_preview("r2", request, reference_date=request.reference_date)


@router.post(
    "/r2/generate", response_model=ReportDocument, summary="R2 本命使用说明书 · 生成完整报告"
)
async def report_r2_generate(request: BaziNatalRequest) -> ReportDocument:
    """生成完整《本命使用说明书》+ 签名交付链接。"""
    require_self_service()
    return compose_report("r2", request, reference_date=request.reference_date)


@router.post(
    "/r3/preview", response_model=ReportPreview, summary="R3 未来12个月时间地图 · 免费预览"
)
async def report_r3_preview(request: ReportTimeRequest) -> ReportPreview:
    """岁运输入的免费预览：年度主题 + 高杠杆/低能量窗口（PRD §3A.4）。"""
    return compose_preview("r3", request, reference_date=request.reference_date)


@router.post(
    "/r3/generate", response_model=ReportDocument, summary="R3 未来12个月时间地图 · 生成完整报告"
)
async def report_r3_generate(request: ReportTimeRequest) -> ReportDocument:
    """生成完整《未来12个月时间地图》+ 签名交付链接。"""
    require_self_service()
    return compose_report("r3", request, reference_date=request.reference_date)


# Fulfilment routes use the same report prefix; their bodies never persist raw chart inputs.


def issue(product, request):
    return save_delivery(
        get_settings().report_store_path, compose_report(product, request, request.reference_date)
    )


@router.post("/r1/issue", response_model=ReportDocument, dependencies=[Depends(require_operator)])
def issue_r1(request: ReportRelationshipRequest):
    return issue("r1", request)


@router.post("/r2/issue", response_model=ReportDocument, dependencies=[Depends(require_operator)])
def issue_r2(request: BaziNatalRequest):
    return issue("r2", request)


@router.post("/r3/issue", response_model=ReportDocument, dependencies=[Depends(require_operator)])
def issue_r3(request: ReportTimeRequest):
    return issue("r3", request)


@router.post("/{product}/delivery/{delivery_id}", response_model=ReportDocument)
def fetch_delivery(product: ReportProduct, delivery_id: str, request: DeliveryLookup):
    document = load_delivery(get_settings().report_store_path, product, delivery_id, request.token)
    if document is None:
        raise ReportDeliveryError("交付链接无效、已撤销或已过期，请联系交付人员。")
    return document


@router.post("/delivery/{delivery_id}/revoke", dependencies=[Depends(require_operator)])
def revoke(delivery_id: str):
    if not revoke_delivery(get_settings().report_store_path, delivery_id):
        raise ReportDeliveryError("未找到该交付记录。")
    return {"status": "revoked"}


@router.get("/{product}/sample", response_model=ReportDocument)
def report_sample(product: ReportProduct):
    """A public, labelled chart example computed by the same report engine."""
    natal = dict(
        birth_date="1988-02-15",
        birth_time="23:30:00",
        city="成都",
        gender="male",
        reference_date="2026-10-01",
    )
    if product == "r1":
        request = BaziHehunRequest.model_validate(
            {
                "male": {"birth_date": "1988-02-15", "birth_time": "23:30:00", "city": "成都"},
                "female": {"birth_date": "1990-06-15", "birth_time": "10:00:00", "city": "北京"},
                "reference_date": "2026-10-01",
            }
        )
    elif product == "r2":
        request = BaziNatalRequest.model_validate(natal)
    else:
        request = ReportTimeRequest.model_validate(
            {
                **natal,
                "start_date": "2026-10-01",
                "start_year": 2026,
                "end_year": 2027,
                "focus_year": 2026,
            }
        )
    doc = compose_report(product, request, request.reference_date)
    return doc.model_copy(
        update={
            "order_id": "sample",
            "token": "",
            "expires_at": "",
            "generated_date": request.reference_date.isoformat(),
        }
    )


def _verify_and_compose(
    product: ReportProduct, order_id: str, token: str, request
) -> ReportDocument:
    """验签 + 校验输入与订单匹配后重算报告（三个 fetch 端点共用的同一段判断）。

    v1 无存储（后端零数据库），「链接」= 订单号 + 签名令牌 + 输入（输入由前端本地暂存，
    人工交付时随链接一并说明）。`order_id` 必须与本次输入的规范哈希一致，否则视为
    链接与输入不匹配。Phase 2 引入输入暂存后本端点契约不变，只是不再要求请求体。
    """
    require_self_service()
    settings = get_settings()
    if not verify_token(
        settings.report_secret, product, order_id, token, settings.report_link_ttl_hours
    ):
        raise HTTPException(status_code=404, detail="report link invalid or expired")
    if derive_order_id(product, request) != order_id:
        raise HTTPException(status_code=404, detail="report order does not match input")
    return compose_report(product, request, reference_date=getattr(request, "reference_date", None))


@router.post("/r1/{order_id}", response_model=ReportDocument, summary="凭 R1 签名链接取回报告")
async def report_fetch_r1(
    order_id: str, token: str, request: ReportRelationshipRequest
) -> ReportDocument:
    return _verify_and_compose("r1", order_id, token, request)


@router.post("/r2/{order_id}", response_model=ReportDocument, summary="凭 R2 签名链接取回报告")
async def report_fetch_r2(order_id: str, token: str, request: BaziNatalRequest) -> ReportDocument:
    return _verify_and_compose("r2", order_id, token, request)


@router.post("/r3/{order_id}", response_model=ReportDocument, summary="凭 R3 签名链接取回报告")
async def report_fetch_r3(order_id: str, token: str, request: ReportTimeRequest) -> ReportDocument:
    return _verify_and_compose("r3", order_id, token, request)
