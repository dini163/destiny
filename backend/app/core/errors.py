"""Domain exceptions raised by computation engines, and their HTTP mapping."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DestinyError(Exception):
    """Base class for every domain error raised by a computation engine."""

    status_code: int = 400
    code: str = "destiny_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


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


def register_error_handlers(app: FastAPI) -> None:
    """Map :class:`DestinyError` subclasses to a consistent JSON error envelope."""

    @app.exception_handler(DestinyError)
    async def handle_destiny_error(_request: Request, exc: DestinyError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )
