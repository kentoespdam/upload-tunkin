"""
Shim module — re-exports from app/responses/ for backward compatibility.

Will be cleaned up after all routers have migrated to domain modules.
"""

# Re-export all schemas (pure Pydantic types)
from app.responses.schemas import (  # noqa: F401
    AuthRequest,
    BasePageResponse,
    BaseResponse,
    BaseToken,
    PageResponse,
    RefreshTokenRequest,
    Token,
    TokenPayload,
    TunkinModel,
    User,
    UserInDb,
)

# Re-export builder
from app.responses.builder import ResponseBuilder, get_response_builder  # noqa: F401

# Re-export error utilities
from app.responses.errors import (  # noqa: F401
    CustomException,
    bad_request,
    conflict,
    forbidden,
    from_exception,
    from_http_exception,
    internal_server_error,
    not_found,
    unauthorized,
    unprocessable_entity,
    validation_error,
)

# ── Patch error methods onto ResponseBuilder ───────────────────
# These are regular (non-classmethod) static-style functions that
# use the errors module's own `_status_handlers` registry.
# This preserves the ResponseBuilder.bad_request() API for existing
# call-sites without needing a classmethod binding.
ResponseBuilder.bad_request = bad_request              # type: ignore[attr-defined]
ResponseBuilder.unauthorized = unauthorized             # type: ignore[attr-defined]
ResponseBuilder.forbidden = forbidden                   # type: ignore[attr-defined]
ResponseBuilder.not_found = not_found                   # type: ignore[attr-defined]
ResponseBuilder.conflict = conflict                     # type: ignore[attr-defined]
ResponseBuilder.unprocessable_entity = unprocessable_entity  # type: ignore[attr-defined]
ResponseBuilder.internal_server_error = internal_server_error  # type: ignore[attr-defined]
ResponseBuilder.validation_error = validation_error     # type: ignore[attr-defined]
ResponseBuilder.from_http_exception = from_http_exception  # type: ignore[attr-defined]
ResponseBuilder.from_exception = from_exception         # type: ignore[attr-defined]
