from typing import Annotated

from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.params import Form
from starlette import status
from starlette.responses import FileResponse

from app import TunkinRepository
from app.core.config import LOGGER
from app.models.request_model import TunkinRequest, TunkinUploadRequest
from app.models.response_model import User, ResponseBuilder, get_response_builder
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
    # except HTTPException as e:
    #     LOGGER.error(e)
    #     return response_builder.from_exception(e)
    except Exception as e:
        LOGGER.error(e)
        return response_builder.from_exception(e)


@router.get("/exists/{periode}", summary="Data Tunkin")
async def check_exist(
        periode: str,
        user: Annotated[User, Depends(require_role(["payrollprocess"]))],
        response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)]
):
    result = await repository.check_exist_tunkin(periode)
    return response_builder.success(result)


@router.post("/upload", summary="Upload File Excel Tunkin")
async def upload_file(req: Annotated[TunkinUploadRequest, Form()],
                      user: Annotated[User, Depends(require_role(["payrollprocess"]))],
                      response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)]):
    try:
        result = await repository.upload(req)
        return response_builder.success(result)
    except HTTPException as e:
        if e.status_code == status.HTTP_400_BAD_REQUEST:
            return response_builder.bad_request(e.detail)
        if e.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
            return response_builder.internal_server_error(e.detail)

@router.get("/download/template", summary="Download Template Excel Tunkin")
async def download_template(
        user: Annotated[User, Depends(require_role(["payrollprocess"]))],
):
    return FileResponse("template/template.xlsx", filename="template_tunkin.xlsx")