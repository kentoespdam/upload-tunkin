from typing import Annotated

from fastapi import APIRouter, UploadFile, Query, Depends, HTTPException
from starlette import status

from app import TunkinRepository
from app.core.config import LOGGER
from app.models.request_model import TunkinRequest, User
from app.models.response_model import ResponseBuilder, get_response_builder
from app.repositories.sys_user import require_role

router = APIRouter(
    prefix="/tunkin",
    tags=["Tunkin Endpoints"],
    responses={404: {"description": "Not found"}},
)

repository = TunkinRepository()


@router.get("/{periode}", summary="Data Tunkin")
def upload_file(periode: str,
                query: Annotated[TunkinRequest, Query()],
                user: Annotated[User, Depends(require_role(["payrollprocess"]))],
                response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)]):
    try:
        result = repository.fetch_page_data(periode, query)
        return response_builder.paginated(result)
    except HTTPException as e:
        LOGGER.error(e)
        if e.status_code == status.HTTP_400_BAD_REQUEST:
            return response_builder.bad_request(e.detail)
        if e.status_code == status.HTTP_403_FORBIDDEN:
            return response_builder.forbidden(e.detail)
    except Exception as e:
        LOGGER.error(e)
        return response_builder.internal_server_error("An error occurred while processing the request.")


@router.post("/upload", summary="Upload File Excel Tunkin")
async def upload_file(file: UploadFile,
                      user: Annotated[User, Depends(require_role(["payrollprocess"]))],
                      response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)]):
    try:
        result = await repository.upload(file)
        return response_builder.success(result)
    except HTTPException as e:
        if e.status_code == status.HTTP_400_BAD_REQUEST:
            return response_builder.bad_request(e.detail)
        if e.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            return response_builder.internal_server_error(e.detail)
