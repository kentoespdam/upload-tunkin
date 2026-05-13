
from fastapi import FastAPI, HTTPException
from jwt import ExpiredSignatureError, PyJWTError

from app.core.config import LOGGER, Config
from app.core.cors import configure_cors
from app.models.response_model import ResponseBuilder
from app.organization import router as organization_router
from app.auth import router as auth_router
from app.tunkin import router as tunkin_router

app = FastAPI(
    title="Upload Tunkin API",
)

configure_cors(app, Config())


@app.exception_handler(HTTPException)
async def http_exception_handler(_request, exc: HTTPException):
    LOGGER.error(f"http exception: {exc.detail}")
    return ResponseBuilder.from_http_exception(exc)


@app.exception_handler(PyJWTError)
async def jwt_exception_handler(_request, exc: PyJWTError):
    LOGGER.error(f"jwt exception: {', '.join(exc.args)}")
    if isinstance(exc, ExpiredSignatureError):
        message = "Token has expired"
    else:
        message = ", ".join(exc.args)
    return ResponseBuilder.unauthorized(message, headers={"WWW-Authenticate": "Bearer"})


@app.exception_handler(Exception)
async def generic_exception_handler(_request, exc: Exception):
    """Catch-all for unexpected errors — logs and returns 500."""
    LOGGER.error(f"Unhandled exception: {exc}")
    return ResponseBuilder.from_exception(exc)


@app.get("/")
def index():
    return {"Hello": "World"}


app.include_router(auth_router.router)
app.include_router(tunkin_router.router)
app.include_router(organization_router.router)
