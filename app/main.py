
from fastapi import FastAPI, HTTPException
from jwt import ExpiredSignatureError, InvalidTokenError, DecodeError
from starlette.middleware.cors import CORSMiddleware

from app.core.config import LOGGER
from app.models.response_model import ResponseBuilder
from app.routers import tunkin, auth, organization

app = FastAPI(
    title="Upload Tunkin API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*']
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    LOGGER.error(f"http exception: {exc.detail}")
    res = ResponseBuilder()
    return res.from_http_exception(exc)

@app.exception_handler(ExpiredSignatureError)
async def expired_signature_exception_handler(request, exc: ExpiredSignatureError):
    LOGGER.error(f"http exception: {", ".join(exc.args)}")
    res = ResponseBuilder()
    return res.unauthorized(", ".join(exc.args), headers={"WWW-Authenticate": "Bearer"})


@app.exception_handler(InvalidTokenError)
async def expired_signature_exception_handler(request, exc: InvalidTokenError):  # noqa: F811
    LOGGER.error(f"http exception: {", ".join(exc.args)}")
    res = ResponseBuilder()
    return res.unauthorized(", ".join(exc.args), headers={"WWW-Authenticate": "Bearer"})


@app.exception_handler(DecodeError)
async def expired_signature_exception_handler(request, exc: DecodeError):  # noqa: F811
    LOGGER.error(f"http exception: {", ".join(exc.args)}")
    res = ResponseBuilder()
    return res.unauthorized(", ".join(exc.args), headers={"WWW-Authenticate": "Bearer"})


@app.get("/")
def index():
    return {"Hello": "World"}


app.include_router(auth.router)
app.include_router(tunkin.router)
app.include_router(organization.router)
