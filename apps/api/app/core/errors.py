from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.domain import ErrorResponse


def api_error_detail(
    code: str,
    message: str,
    details: dict | list | str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        payload["details"] = details
    return payload


def _status_to_error_code(status_code: int) -> str:
    if status_code == 400:
        return "bad_request"
    if status_code == 404:
        return "not_found"
    if status_code == 422:
        return "validation_error"
    if status_code >= 500:
        return "internal_error"
    return "api_error"


def _build_error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict | list | str | None = None,
) -> JSONResponse:
    body = ErrorResponse(error={"code": code, "message": message, "details": details})
    return JSONResponse(status_code=status_code, content=body.model_dump(exclude_none=True))


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict) and "code" in detail and "message" in detail:
            return _build_error_response(
                status_code=exc.status_code,
                code=str(detail["code"]),
                message=str(detail["message"]),
                details=detail.get("details"),
            )

        message = str(detail) if detail is not None else "Request failed"
        return _build_error_response(
            status_code=exc.status_code,
            code=_status_to_error_code(exc.status_code),
            message=message,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(
        _: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return _build_error_response(
            status_code=422,
            code="validation_error",
            message="Request validation failed",
            details={"issues": exc.errors()},
        )


COMMON_ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Bad request"},
    404: {"model": ErrorResponse, "description": "Resource not found"},
    422: {"model": ErrorResponse, "description": "Validation error"},
    500: {"model": ErrorResponse, "description": "Internal server error"},
}
