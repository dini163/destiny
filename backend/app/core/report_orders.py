"""无状态订单：输入规范哈希 + HMAC 签名链接（v1「订单 + 签名交付链接」的载体）。

后端零数据库（AGENTS.md 分层无存储层），v1 的订单就做成「凭据 + 重算」：
`order_id` 由输入的规范 JSON 确定性派生（同一输入恒同），`token` 是服务端密钥对
`product:order_id:created_ts` 的 HMAC 签名，取报告时验签通过即按同一输入重新生成 ——
引擎是确定性的，所以不需要存储任何订单行。撤销 = 过期时间已过（或密钥轮换后旧签全部失效）。

`token` 自带时间：它编码成 `<b64(created_ts)>.<sig>`，`verify_token` 先从令牌拆出创建时间，
再重算签名并检查过期 —— 因此取报告只需 `order_id + token` 两个参数，不需要额外状态。

安全说明：`REPORT_SECRET` 只从环境变量读；缺省值是开发用占位，生产环境必须设置，
否则签名链接对任何知道代码的人可伪造（.env.example 已标注）。
"""

import base64
import hashlib
import hmac
from datetime import datetime, timedelta, timezone

from app.schemas.report import ReportProduct


def canonical_input(product: ReportProduct, request) -> str:
    """把入参冻结成规范哈希：排除 None、ISO 时间、pydantic 固定字段序 —— 同一输入恒同。

    用 `model_dump_json(exclude_none=True)`：pydantic 按字段定义序输出，字段名与值就是
    「输入规范」，报告版本号另存于 `content.report_templates.REPORT_VERSION`，两者一起
    决定可复现性。不显式排序键 —— 同一 schema 的字段序固定，排序只是多余的稳定性承诺。
    """
    payload = request.model_dump_json(exclude_none=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def derive_order_id(product: ReportProduct, request) -> str:
    """订单号 = 输入规范哈希前 16 位；同一输入恒同，便于对账与重取。"""
    return canonical_input(product, request)[:16]


def _sign_raw(secret: str, product: ReportProduct, order_id: str, created_ts: str) -> str:
    """对 `product:order_id:created_ts` 签名；`created_ts` 为 ISO（UTC）。"""
    message = f"{product}:{order_id}:{created_ts}"
    return hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()


def _encode_created(created_at: datetime) -> str:
    """创建时间编码进令牌前段（URL-safe base64），验签时拆出即可，无需外部状态。"""
    raw = created_at.astimezone(timezone.utc).isoformat().encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii")


def _decode_created(segment: str) -> str | None:
    try:
        return base64.urlsafe_b64decode(segment.encode("ascii")).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None


def sign_token(secret: str, product: ReportProduct, order_id: str, created_at: datetime) -> str:
    """生成 `<b64(created_ts)>.<sig>` 形式的签名令牌。"""
    created_ts = created_at.astimezone(timezone.utc).isoformat()
    encoded = _encode_created(created_at)
    sig = _sign_raw(secret, product, order_id, created_ts)
    return f"{encoded}.{sig}"


def verify_token(
    secret: str, product: ReportProduct, order_id: str, token: str, ttl_hours: int
) -> bool:
    """验签 + 过期检查：从令牌拆出创建时间，重算签名逐字节比对（防时序侧信道）。

    签名不匹配或已过期都返回 False —— 调用方不必区分「伪造」与「过期」，只给 404。
    """
    try:
        encoded, sig = token.split(".", 1)
    except ValueError:
        return False
    created_ts = _decode_created(encoded)
    if created_ts is None:
        return False
    expected = _sign_raw(secret, product, order_id, created_ts)
    if not hmac.compare_digest(expected, sig):
        return False
    try:
        created_at = datetime.fromisoformat(created_ts)
    except ValueError:
        return False
    now = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(hours=ttl_hours)
    return now < expires_at


def expires_at_for(created_at: datetime, ttl_hours: int) -> str:
    """交付链接的过期时间（ISO，UTC），随报告返回给前端展示。"""
    return (created_at.astimezone(timezone.utc) + timedelta(hours=ttl_hours)).isoformat()
