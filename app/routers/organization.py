from typing import Annotated

from fastapi import APIRouter, Depends

from app.models.response_model import ResponseBuilder, User, get_response_builder
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.sys_user import require_any_role

router=APIRouter(
    prefix="/organization",
    tags=["Organization Endpoints"],
    responses={404: {"description": "Not found"}},
)

@router.get("/list", summary="List Organization")
async def fetch_list_organization(
    user: Annotated[User, Depends(require_any_role)],
    repository:Annotated[OrganizationRepository, Depends()],
    response_builder:Annotated[ResponseBuilder, Depends(get_response_builder)]
    ):
    try:
        data=await repository.fetch_all()
        if data.empty:
            return response_builder.not_found("Organization not found")
        return response_builder.success(data=data.to_dict("records"), message="Organization list")
    except Exception as e:
        return response_builder.from_exception(e)