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


def register_error_handlers(app: FastAPI) -> None:
    """Map :class:`DestinyError` subclasses to a consistent JSON error envelope."""

    @app.exception_handler(DestinyError)
    async def handle_destiny_error(_request: Request, exc: DestinyError) -> JSONResponse:
        error: dict[str, object] = {"code": exc.code, "message": exc.message}
        if exc.context is not None:
            error["context"] = exc.context
        return JSONResponse(status_code=exc.status_code, content={"error": error})
