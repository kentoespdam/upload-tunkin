import uuid
from collections.abc import Mapping
from datetime import datetime
from typing import Optional, Union, List, Dict, Any, Hashable

from pydantic import BaseModel
from starlette.responses import JSONResponse


class BaseResponse(BaseModel):
    status: int
    data: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None
    errors: Optional[Union[str, List[str]]] = None
    message: Optional[str] = None
    timestamp: str = None
    request_id: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BasePageResponse(BaseModel):
    content: List[Dict[Union[str, Hashable], Any]]
    total: int
    page: int
    page_size: int
    total_pages: int


class PageResponse(BaseResponse):
    data: BasePageResponse


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
        """
        Build success response

        Args:
            status: HTTP status code
            data: Response data
            message: Success message
            headers: Additional headers
            request_id: Request ID for tracing
        """
        content = BaseResponse(
            status=status,
            data=data,
            errors=None,
            message=message,
            timestamp=ResponseBuilder._get_timestamp(),
            request_id=request_id or ResponseBuilder._generate_request_id()
        )

        # Set default headers
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

    @staticmethod
    def error(
            status: int = 400,
            errors: Optional[Union[str, List[str]]] = None,
            message: Optional[str] = None,
            headers: Optional[Mapping[str, str]] = None,
            request_id: Optional[str] = None) -> JSONResponse:
        """
        Build error response

        Args:
            status: HTTP status code
            errors: Error messages (string or list of strings)
            message: Overall error message
            error_details: Detailed error information
            headers: Additional headers
            request_id: Request ID for tracing
        """
        # Convert single error string to list
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

    # Predefined error responses
    @staticmethod
    def bad_request(
            errors: Union[str, List[str]] = "Bad request",
            message: str = "The request was invalid",
            headers: Optional[Mapping[str, str]] = None,
            request_id: Optional[str] = None) -> JSONResponse:
        """400 Bad Request"""
        return ResponseBuilder.error(
            status=ResponseBuilder.HTTP_400_BAD_REQUEST,
            errors=errors,
            message=message,
            headers=headers,
            request_id=request_id
        )

    @staticmethod
    def unauthorized(
            errors: Union[str, List[str]] = "Unauthorized",
            message: str = "Authentication required",
            headers: Optional[Mapping[str, str]] = None,
            request_id: Optional[str] = None) -> JSONResponse:
        """401 Unauthorized"""
        return ResponseBuilder.error(
            status=ResponseBuilder.HTTP_401_UNAUTHORIZED,
            errors=errors,
            message=message,
            headers=headers,
            request_id=request_id
        )

    @staticmethod
    def forbidden(
            errors: Union[str, List[str]] = "Forbidden",
            message: str = "Access denied",
            headers: Optional[Mapping[str, str]] = None,
            request_id: Optional[str] = None) -> JSONResponse:
        """403 Forbidden"""
        return ResponseBuilder.error(
            status=ResponseBuilder.HTTP_403_FORBIDDEN,
            errors=errors,
            message=message,
            headers=headers,
            request_id=request_id
        )

    @staticmethod
    def not_found(
            errors: Union[str, List[str]] = "Resource not found",
            message: str = "The requested resource was not found",
            headers: Optional[Mapping[str, str]] = None,
            request_id: Optional[str] = None) -> JSONResponse:
        """404 Not Found"""
        return ResponseBuilder.error(
            status=ResponseBuilder.HTTP_404_NOT_FOUND,
            errors=errors,
            message=message,
            headers=headers,
            request_id=request_id
        )

    @staticmethod
    def conflict(
            errors: Union[str, List[str]] = "Conflict",
            message: str = "Resource conflict occurred",
            headers: Optional[Mapping[str, str]] = None,
            request_id: Optional[str] = None) -> JSONResponse:
        """409 Conflict"""
        return ResponseBuilder.error(
            status=ResponseBuilder.HTTP_409_CONFLICT,
            errors=errors,
            message=message,
            headers=headers,
            request_id=request_id
        )

    @staticmethod
    def unprocessable_entity(
            errors: Union[str, List[str]] = "Unprocessable entity",
            message: str = "The request could not be processed",
            headers: Optional[Mapping[str, str]] = None,
            request_id: Optional[str] = None) -> JSONResponse:
        """422 Unprocessable Entity"""
        return ResponseBuilder.error(
            status=ResponseBuilder.HTTP_422_UNPROCESSABLE_ENTITY,
            errors=errors,
            message=message,
            headers=headers,
            request_id=request_id
        )

    @staticmethod
    def internal_server_error(
            errors: Union[str, List[str]] = "Internal server error",
            message: str = "An internal server error occurred",
            headers: Optional[Mapping[str, str]] = None,
            request_id: Optional[str] = None) -> JSONResponse:
        """500 Internal Server Error"""
        return ResponseBuilder.error(
            status=ResponseBuilder.HTTP_500_INTERNAL_SERVER_ERROR,
            errors=errors,
            message=message,
            headers=headers,
            request_id=request_id
        )

    @staticmethod
    def validation_error(
            field_errors: Dict[str, str],
            message: str = "Validation failed") -> JSONResponse:
        """422 Validation Error with field-specific details"""

        return ResponseBuilder.unprocessable_entity(
            errors="Validation error",
            message=message,
        )


def get_response_builder() -> ResponseBuilder:
    return ResponseBuilder()


class CustomException(Exception):
    def __init__(self, message: Optional[str] = None):
        self.message = message
