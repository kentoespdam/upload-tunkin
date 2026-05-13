from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.security import get_current_user_from_token
from app.organization.repository import list_organizations
from app.responses.builder import ResponseBuilder
from app.responses.schemas import User

router = APIRouter(
    prefix="/organization",
    tags=["Organization"],
)


@router.get("")
def get_organizations(
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    orgs: Annotated[list[dict], Depends(list_organizations)],
):
    """List all organizations. Requires valid JWT token (any role)."""
    return ResponseBuilder.ok(data=orgs)
