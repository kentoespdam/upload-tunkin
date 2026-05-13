from typing import Callable, Dict, List, Optional, Union

from fastapi import HTTPException
from starlette.responses import JSONResponse

from app.responses.builder import ResponseBuilder


class CustomException(Exception):
    def __init__(self, message: Optional[str] = None):
        self.message = message


# ── Predefined error responses ─────────────────────────────────

_status_handlers: dict[int, Callable[..., JSONResponse]] = {}


def _build_registry():
    if _status_handlers:
        return
    _status_handlers.update({
        400: bad_request,
        401: unauthorized,
        403: forbidden,
        404: not_found,
        409: conflict,
        422: unprocessable_entity,
    })


def bad_request(
        errors: Union[str, List[str]] = "Bad request",
        message: str = "The request was invalid",
        headers: Optional[Dict[str, str]] = None,
        request_id: Optional[str] = None) -> JSONResponse:
    """400 Bad Request"""
    return ResponseBuilder.error(
        status=ResponseBuilder.HTTP_400_BAD_REQUEST,
        errors=errors, message=message, headers=headers, request_id=request_id
    )


def unauthorized(
        errors: Union[str, List[str]] = "Unauthorized",
        message: str = "Authentication required",
        headers: Optional[Dict[str, str]] = None,
        request_id: Optional[str] = None) -> JSONResponse:
    """401 Unauthorized"""
    return ResponseBuilder.error(
        status=ResponseBuilder.HTTP_401_UNAUTHORIZED,
        errors=errors, message=message, headers=headers, request_id=request_id
    )


def forbidden(
        errors: Union[str, List[str]] = "Forbidden",
        message: str = "Access denied",
        headers: Optional[Dict[str, str]] = None,
        request_id: Optional[str] = None) -> JSONResponse:
    """403 Forbidden"""
    return ResponseBuilder.error(
        status=ResponseBuilder.HTTP_403_FORBIDDEN,
        errors=errors, message=message, headers=headers, request_id=request_id
    )


def not_found(
        errors: Union[str, List[str]] = "Resource not found",
        message: str = "The requested resource was not found",
        headers: Optional[Dict[str, str]] = None,
        request_id: Optional[str] = None) -> JSONResponse:
    """404 Not Found"""
    return ResponseBuilder.error(
        status=ResponseBuilder.HTTP_404_NOT_FOUND,
        errors=errors, message=message, headers=headers, request_id=request_id
    )


def conflict(
        errors: Union[str, List[str]] = "Conflict",
        message: str = "Resource conflict occurred",
        headers: Optional[Dict[str, str]] = None,
        request_id: Optional[str] = None) -> JSONResponse:
    """409 Conflict"""
    return ResponseBuilder.error(
        status=ResponseBuilder.HTTP_409_CONFLICT,
        errors=errors, message=message, headers=headers, request_id=request_id
    )


def unprocessable_entity(
        errors: Union[str, List[str]] = "Unprocessable entity",
        message: str = "The request could not be processed",
        headers: Optional[Dict[str, str]] = None,
        request_id: Optional[str] = None) -> JSONResponse:
    """422 Unprocessable Entity"""
    return ResponseBuilder.error(
        status=ResponseBuilder.HTTP_422_UNPROCESSABLE_ENTITY,
        errors=errors, message=message, headers=headers, request_id=request_id
    )


def internal_server_error(
        errors: Union[str, List[str]] = "Internal server error",
        message: str = "An internal server error occurred",
        headers: Optional[Dict[str, str]] = None,
        request_id: Optional[str] = None) -> JSONResponse:
    """500 Internal Server Error"""
    return ResponseBuilder.error(
        status=ResponseBuilder.HTTP_500_INTERNAL_SERVER_ERROR,
        errors=errors, message=message, headers=headers, request_id=request_id
    )


def validation_error(
        errors: Union[str, List[str]] = "Validation error",
        message: str = "Validation failed",
        headers: Optional[Dict[str, str]] = None,
        request_id: Optional[str] = None) -> JSONResponse:
    """422 Validation Error"""
    return ResponseBuilder.error(
        status=ResponseBuilder.HTTP_422_UNPROCESSABLE_ENTITY,
        errors=errors, message=message, headers=headers, request_id=request_id
    )


# ── Error dispatchers ──────────────────────────────────────────

def from_http_exception(ex: HTTPException) -> JSONResponse:
    """Build response from HTTPException using the status-code registry."""
    _build_registry()
    handler = _status_handlers.get(
        ex.status_code,
        internal_server_error,
    )
    return handler(errors=ex.detail, headers=ex.headers)


def from_exception(exc: Exception) -> JSONResponse:
    """Build response from exception"""
    return internal_server_error(
        errors=str(exc),
        message="An error occurred"
    )
