
from fastapi import FastAPI, HTTPException
from jwt import ExpiredSignatureError, PyJWTError

from app.core.config import LOGGER, Config
from app.core.cors import configure_cors
from app.models.response_model import ResponseBuilder
from app.routers import tunkin, auth

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


@app.get("/")
def index():
    return {"Hello": "World"}


app.include_router(auth.router)
app.include_router(tunkin.router)
