from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Query
from fastapi.security import OAuth2PasswordRequestForm
from jwt import ExpiredSignatureError, InvalidTokenError, DecodeError
from starlette import status

from app.core.config import Config, LOGGER
from app.core.security import (
    TokenIssuer, TokenVerifier,
    get_token_issuer, get_token_verifier,
    get_current_user_from_token,
    get_sys_user_repository,
)
from app.models.response_model import (
    User, Token, BaseToken, RefreshTokenRequest,
    get_response_builder, ResponseBuilder,
)
from app.repositories.sys_user import SysUserRepository

router = APIRouter(
    tags=["Authentication Endpoints"],
    responses={404: {"description": "Not found"}},
)


def get_config() -> Config:
    return Config()


@router.post("/token", summary="Authenticate User and Get Tokens", response_model=Token)
def authenticate_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_repo: Annotated[SysUserRepository, Depends(get_sys_user_repository)],
    issuer: Annotated[TokenIssuer, Depends(get_token_issuer)],
    config: Annotated[Config, Depends(get_config)],
) -> Token:
    # Validate client credentials
    is_match_client_id = config.jwt_client_id == form_data.client_id
    is_match_client_secret = config.jwt_client_secret == form_data.client_secret
    if not is_match_client_id or not is_match_client_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials",
        )

    # Authenticate user
    user = user_repo.authenticate(form_data)
    if user.get("disabled", True):
        raise HTTPException(status_code=401, detail="Inactive user")

    try:
        _access_token = issuer.issue_access(
            user,
            timedelta(minutes=config.jwt_access_token_expire_minutes),
        )
        _refresh_token = issuer.issue_refresh(
            user,
            timedelta(days=7),
        )
        return Token(
            access_token=_access_token,
            refresh_token=_refresh_token,
            token_type="bearer",
            expires_in=config.jwt_access_token_expire_minutes * 60,
        )
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"Error creating tokens: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create tokens",
        )


@router.post(
    "/refresh",
    summary="Refresh Access Token",
    response_model=BaseToken,
    responses={401: {"description": "Invalid or expired refresh token"}},
)
async def refresh_token(
    req: RefreshTokenRequest,
    verifier: Annotated[TokenVerifier, Depends(get_token_verifier)],
    issuer: Annotated[TokenIssuer, Depends(get_token_issuer)],
    config: Annotated[Config, Depends(get_config)],
    user_repo: Annotated[SysUserRepository, Depends(get_sys_user_repository)],
) -> BaseToken:
    try:
        payload = verifier.verify(req.token)
        if payload.get("type") != "refresh_token":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        username = payload.get("sub")
        user = user_repo.get_user(username)

        if not user:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        new_access_token = issuer.issue_access(user)

        return BaseToken(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=config.jwt_access_token_expire_minutes * 60,
        )
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token has expired")
    except (InvalidTokenError, DecodeError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"Error refreshing token: {e}")
        raise HTTPException(status_code=401, detail="Could not refresh token")


@router.get(
    "/me",
    responses={401: {"description": "Unauthorized"}, 400: {"description": "Inactive user"}},
)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)],
):
    try:
        return response_builder.ok(data=current_user.model_dump())
    except HTTPException as e:
        LOGGER.error(e)
        return response_builder.from_http_exception(e)


@router.options("/validate", summary="Validate token")
async def validate_token(
    req: Annotated[RefreshTokenRequest, Query()],
    verifier: Annotated[TokenVerifier, Depends(get_token_verifier)],
    response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)],
):
    try:
        payload = verifier.verify(req.token)

        content = {
            "valid": True,
            "username": payload.get("sub"),
            "role": payload.get("role"),
            "expires_at": payload.get("exp"),
            "token_type": payload.get("type"),
        }
        return response_builder.ok(data=content)
    except ExpiredSignatureError:
        return response_builder.ok({"valid": False, "error": "Token has expired"})
    except (InvalidTokenError, DecodeError):
        return response_builder.ok({"valid": False, "error": "Invalid token"})
    except Exception as e:
        LOGGER.error(f"Error validating token: {e}")
        return response_builder.ok({"valid": False, "error": "Token validation error"})