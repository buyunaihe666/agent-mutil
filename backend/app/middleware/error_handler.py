"""Global exception handlers for FastAPI application."""

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = structlog.get_logger(__name__)


class AppError(Exception):
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        detail: dict | None = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.detail = detail or {}


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found", detail: dict | None = None):
        super().__init__(message, code="NOT_FOUND", status_code=404, detail=detail)


class ValidationError(AppError):
    def __init__(self, message: str = "Validation failed", detail: dict | None = None):
        super().__init__(message, code="VALIDATION_ERROR", status_code=400, detail=detail)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized", detail: dict | None = None):
        super().__init__(message, code="UNAUTHORIZED", status_code=401, detail=detail)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden", detail: dict | None = None):
        super().__init__(message, code="FORBIDDEN", status_code=403, detail=detail)


def _error_response(
    status_code: int, code: str, message: str, detail: dict | None = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "detail": detail or {},
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "Application error",
            code=exc.code,
            message=exc.message,
            path=str(request.url.path),
        )
        return _error_response(exc.status_code, exc.code, exc.message, exc.detail)

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        logger.warning("Validation error", error=str(exc), path=str(request.url.path))
        return _error_response(400, "VALIDATION_ERROR", str(exc))

    @app.exception_handler(KeyError)
    async def key_error_handler(request: Request, exc: KeyError) -> JSONResponse:
        logger.warning("Key error", error=str(exc), path=str(request.url.path))
        return _error_response(404, "NOT_FOUND", f"Key not found: {exc}")

    @app.exception_handler(FileNotFoundError)
    async def file_not_found_handler(request: Request, exc: FileNotFoundError) -> JSONResponse:
        logger.warning("File not found", error=str(exc), path=str(request.url.path))
        return _error_response(404, "NOT_FOUND", str(exc))

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled exception",
            error=str(exc),
            path=str(request.url.path),
        )
        return _error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")
