"""Domain exceptions raised by computation engines, and their HTTP mapping."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DestinyError(Exception):
    """Base class for every domain error raised by a computation engine."""

    status_code: int = 400
    code: str = "destiny_error"

    def __init__(self, message: str, context: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        #: 机器可读的补充事实（如简繁候选列表）。前端据此渲染按钮，而不是解析文案。
        self.context = context


class InvalidBirthDataError(DestinyError):
    """Birth date/time/coordinate input is missing or out of supported range."""

    code = "invalid_birth_data"


class UnsupportedMethodError(DestinyError):
    """The requested casting / derivation method is not implemented."""

    code = "unsupported_method"
    status_code = 422


class InvalidCastInputError(DestinyError):
    """Casting input (e.g. manual coin throws) is missing or malformed."""

    code = "invalid_cast_input"


class EphemerisError(DestinyError):
    """The astronomical ephemeris could not produce a result."""

    code = "ephemeris_error"
    status_code = 500


class NameInputError(DestinyError):
    """姓名学入参无法核定笔画。

    四个机器码由 `code` 区分（spec §7）：`not_han` / `ambiguous_traditional` /
    `variant_required` / `stroke_unresolved`。文案是给人看的，`context` 才是给机器的。
    """

    status_code = 422

    def __init__(
        self, code: str, message: str, context: dict[str, object] | None = None
    ) -> None:
        super().__init__(message, context)
        self.code = code


class TransitRangeError(DestinyError):
    """岁运、流日、流时与合婚推不出请求要的那段。

    九个机器码由 `code` 区分（岁运 spec §7.2、流日 spec §7.2、流时 spec §7.2、
    合婚 spec §9.3）：`transit_range_reversed` / `transit_range_too_wide` /
    `transit_range_unsupported` / `transit_focus_out_of_range` / `liuri_month_unsupported` /
    `liuri_focus_out_of_month` / `liushi_date_unsupported` / `liushi_hour_out_of_day` /
    `hehun_axis_out_of_range` / `report_month_coverage`。
    它们过不了 pydantic 的字段校验，因为每个字段单独看都合法 —— 坏的是它们之间的关系，
    以及它们与该命盘大运窗口的关系，而窗口是排盘之后才知道的事实。所以这里给 422
    而不是 400：请求成形，只是推不出东西来。
    """

    status_code = 422

    def __init__(
        self, code: str, message: str, context: dict[str, object] | None = None
    ) -> None:
        super().__init__(message, context)
        self.code = code


class NumerologyInputError(DestinyError):
    """数字命理入参里没有一个可计算的拉丁字母（数字命理 spec §7）。

    机器码只有一个：`numerology_no_latin_letters`。纯中文名过得了 pydantic 的长度校验
    —— 它确实非空、确实不超长；坏的是「毕达哥拉斯 1–9 映射定义在拉丁字母表上」这条
    前提，而这条前提只有引擎知道。故给 422 域错误而不是 400 校验错误，分工同
    `NameInputError` 的 `not_han`：长度归 pydantic，字符集归引擎。

    这里不静默返回一份全零命盘：那样一来「输错了」与「算出来了」在响应上完全同形，
    用户永远不会发现要改用拼音。
    """

    code = "numerology_no_latin_letters"
    status_code = 422


class GematriaInputError(DestinyError):
    """卡巴拉 gematria 入参里没有一个可称量的拉丁字母（同 `NumerologyInputError` 的道理）。

    机器码只有一个：`gematria_no_latin_letters`。纯中文或纯符号的词过得了 pydantic 的
    非空/长度校验，坏的是「英文 gematria 的 A=1…Z=26 映射定义在拉丁字母表上」这条前提，
    而这条前提只有引擎知道。故给 422 域错误：长度归 pydantic，字符集归引擎。这里不静默
    返回一份零值映射 —— 那样「没字母」与「算出来是 0」在响应上同形，用户不会想到改用拉丁拼写。
    """

    code = "gematria_no_latin_letters"
    status_code = 422


class ReportAccessError(DestinyError):
    """403: report_operator_required / report_manual_delivery_required deny unavailable fulfilment rights."""

    status_code = 403

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class ReportDeliveryError(DestinyError):
    """404 report_delivery_unavailable: invalid, expired and revoked bearer links share one response."""

    status_code = 404
    code = "report_delivery_unavailable"


def register_error_handlers(app: FastAPI) -> None:
    """Map :class:`DestinyError` subclasses to a consistent JSON error envelope."""

    @app.exception_handler(DestinyError)
    async def handle_destiny_error(_request: Request, exc: DestinyError) -> JSONResponse:
        error: dict[str, object] = {"code": exc.code, "message": exc.message}
        if exc.context is not None:
            error["context"] = exc.context
        return JSONResponse(status_code=exc.status_code, content={"error": error})
