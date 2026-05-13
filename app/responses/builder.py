import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Any, Dict, Hashable, List, Optional, Union

from starlette.responses import JSONResponse

from app.responses.schemas import BasePageResponse, BaseResponse


class ResponseBuilder:
    """Enhanced response builder with consistent API response format"""

    # Common HTTP status codes
    HTTP_200_OK = 200
    HTTP_201_CREATED = 201
    HTTP_204_NO_CONTENT = 204
    HTTP_400_BAD_REQUEST = 400
    HTTP_401_UNAUTHORIZED = 401
    HTTP_403_FORBIDDEN = 403
    HTTP_404_NOT_FOUND = 404
    HTTP_409_CONFLICT = 409
    HTTP_422_UNPROCESSABLE_ENTITY = 422
    HTTP_429_TOO_MANY_REQUESTS = 429
    HTTP_500_INTERNAL_SERVER_ERROR = 500
    HTTP_503_SERVICE_UNAVAILABLE = 503

    @staticmethod
    def _generate_request_id() -> str:
        """Generate unique request ID for tracing"""
        return str(uuid.uuid4())

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in ISO format"""
        return datetime.now().isoformat()

    @staticmethod
    def success(
            data: Optional[Union[List[Dict[str, Any]], Dict[str, Any], BasePageResponse]] = None,
            status: int = 200,
            message: Optional[str] = None,
            headers: Optional[Mapping[str, str]] = None,
            request_id: Optional[str] = None) -> JSONResponse:
        """Build success response"""
        content = BaseResponse(
            status=status,
            data=data,
            errors=None,
            message=message,
            timestamp=ResponseBuilder._get_timestamp(),
            request_id=request_id or ResponseBuilder._generate_request_id()
        )
        default_headers = {
            "Content-Type": "application/json",
            "X-Request-ID": content.request_id
        }
        if headers:
            default_headers.update(headers)
        return JSONResponse(
            status_code=status,
            content=content.model_dump(exclude_none=True),
            headers=default_headers
        )

    @staticmethod
    def created(
            data: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None,
            message: str = "Resource created successfully",
            headers: Optional[Mapping[str, str]] = None,
            request_id: Optional[str] = None) -> JSONResponse:
        """201 Created response"""
        return ResponseBuilder.success(
            status=ResponseBuilder.HTTP_201_CREATED,
            data=data,
            message=message,
            headers=headers,
            request_id=request_id
        )

    @staticmethod
    def ok(
            data: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None,
            message: str = "Request successful",
            headers: Optional[Mapping[str, str]] = None,
            request_id: Optional[str] = None) -> JSONResponse:
        """200 OK response"""
        return ResponseBuilder.success(
            status=ResponseBuilder.HTTP_200_OK,
            data=data,
            message=message,
            headers=headers,
            request_id=request_id
        )

    @staticmethod
    def no_content(
            message: str = "No content",
            headers: Optional[Mapping[str, str]] = None,
            request_id: Optional[str] = None) -> JSONResponse:
        """204 No Content response"""
        return ResponseBuilder.success(
            status=ResponseBuilder.HTTP_204_NO_CONTENT,
            data=None,
            message=message,
            headers=headers,
            request_id=request_id
        )

    @staticmethod
    def paginated(
            data: BasePageResponse,
            message: str = "Paginated data retrieved successfully",
            headers: Optional[Mapping[str, str]] = None) -> JSONResponse:
        from app.core.config import SqidsHelper
        sqids_helper = SqidsHelper()
        for item in data.content:
            if "id" in item:
                item["id"] = sqids_helper.encode(item["id"])
        default_headers = {
            "Content-Type": "application/json",
            "X-Request-ID": ResponseBuilder._generate_request_id()
        }
        if headers:
            default_headers.update(headers)
        return ResponseBuilder.success(
            status=ResponseBuilder.HTTP_200_OK,
            data=data.model_dump(),
            message=message,
            headers=default_headers
        )

    # ── Base error builder ─────────────────────────────────────

    @staticmethod
    def error(
            status: int = 400,
            errors: Optional[Union[str, List[str]]] = None,
            message: Optional[str] = None,
            headers: Optional[Mapping[str, str]] = None,
            request_id: Optional[str] = None) -> JSONResponse:
        """Build error response"""
        if isinstance(errors, str):
            errors = [errors]
        content = BaseResponse(
            status=status,
            data=None,
            errors=errors,
            message=message,
            timestamp=ResponseBuilder._get_timestamp(),
            request_id=request_id or ResponseBuilder._generate_request_id(),
        )
        default_headers = {
            "Content-Type": "application/json",
            "X-Request-ID": content.request_id
        }
        if headers:
            default_headers.update(headers)
        return JSONResponse(
            status_code=status,
            content=content.model_dump(exclude_none=True),
            headers=default_headers
        )


def get_response_builder() -> ResponseBuilder:
    return ResponseBuilder()
