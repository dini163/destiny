"""Fulfilment permissions are checked before any private document is generated."""

import secrets

from fastapi import Header

from app.core.config import get_settings
from app.core.errors import ReportAccessError


def require_operator(x_report_operator_key: str | None = Header(default=None)) -> None:
    configured = get_settings().report_operator_key
    if (
        not configured
        or not x_report_operator_key
        or not secrets.compare_digest(configured.encode(), x_report_operator_key.encode())
    ):
        raise ReportAccessError("report_operator_required", "该操作需要交付管理员权限。")


def require_self_service() -> None:
    if get_settings().app_environment == "production":
        raise ReportAccessError(
            "report_manual_delivery_required", "完整报告由人工确认后交付，请使用收到的交付链接。"
        )
