from typing import Annotated

from fastapi import APIRouter, UploadFile, Query, Depends
from starlette.responses import JSONResponse

from app import TunkinRepository
from app.models.request_model import TunkinRequest, User
from app.models.response_model import PageResponse
from app.repositories.sys_user import require_role

router = APIRouter(
    prefix="/tunkin",
    tags=["Tunkin Endpoints"],
    responses={404: {"description": "Not found"}},
)

repository = TunkinRepository()


@router.get("/{periode}",
            summary="Data Tunkin",
            response_model=PageResponse)
def upload_file(periode: str,
                query: Annotated[TunkinRequest, Query()],
                user: Annotated[User, Depends(require_role(["payrollprocess"]))]):
    return repository.fetch_page_data(periode, query)


@router.post("/upload",
             summary="Upload File Excel Tunkin")
async def upload_file(file: UploadFile):
    result = await repository.upload(file)
    return JSONResponse(content=result, status_code=200)
