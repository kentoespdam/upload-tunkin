from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core.config import Config


def configure_cors(app: FastAPI, config: Config) -> None:
    """Configure CORS middleware on the FastAPI app.

    All CORSMiddleware kwargs are passed explicitly so IDE warnings about
    allow_origins='*' + allow_credentials defaults are avoided.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_allow_origins,
        allow_methods=config.cors_allow_methods,
        allow_headers=config.cors_allow_headers,
        allow_credentials=config.cors_allow_credentials,
        allow_origin_regex=None,
        expose_headers=(),
        max_age=600,
    )
