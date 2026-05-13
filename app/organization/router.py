from typing import Annotated

from fastapi import APIRouter, Depends

from app.organization.repository import list_organizations
from app.responses.builder import ResponseBuilder

router = APIRouter(
    prefix="/organization",
    tags=["Organization"],
)


@router.get("")
def get_organizations(
    orgs: Annotated[list[dict], Depends(list_organizations)],
):
    """List all organizations. Public endpoint (no auth required)."""
    return ResponseBuilder.ok(data=orgs)
