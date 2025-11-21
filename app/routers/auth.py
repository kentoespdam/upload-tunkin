from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.params import Query
from fastapi.security import OAuth2PasswordRequestForm
from jwt import ExpiredSignatureError, InvalidTokenError, DecodeError

from app.core.config import Config, LOGGER
from app.models.request_model import User, Token, BaseToken, RefreshTokenRequest
from app.models.response_model import get_response_builder, ResponseBuilder
from app.repositories.sys_user import SysUserRepository, TokenHelper, require_role

router = APIRouter(
    tags=["Authentication Endpoints"],
    responses={404: {"description": "Not found"}},
)


# Dependency injection
def get_user_repository() -> SysUserRepository:
    return SysUserRepository()


def get_token_helper() -> TokenHelper:
    return TokenHelper()


def get_config() -> Config:
    return Config()


@router.post("/token", summary="Authenticate User and Get Tokens")
def authenticate_user(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        repository: Annotated[SysUserRepository, Depends(get_user_repository)],
        token_helper: Annotated[TokenHelper, Depends(get_token_helper)],
        config: Annotated[Config, Depends(get_config)],
        response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)],
):
    if not token_helper.validata_client(form_data.client_id, form_data.client_secret):
        return response_builder.unauthorized("Invalid client credentials", headers={"WWW-Authenticate": "Bearer)"})

    user = repository.authenticate(form_data)
    if not user:
        return response_builder.unauthorized("Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})

    if user.get("disabled", True):
        return response_builder.bad_request("inactive_user")

    try:
        access_token = token_helper.create_access_token(
            user,
            timedelta(minutes=config.jwt_access_token_expire_minutes)
        )
        refresh_token = token_helper.create_refresh_token(
            user,
            timedelta(days=7)
        )
        token = Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=token_helper.config.jwt_access_token_expire_minutes * 60
        )
        return response_builder.created(data=token.model_dump())

    except Exception as e:
        LOGGER.error(f"Error creating tokens: {e}")
        return response_builder.internal_server_error("could_not_create_tokens")


@router.post(
    "/refresh",
    summary="Refresh Access Token",
    responses={
        401: {"description": "Invalid or expired refresh token"},
    }
)
async def refresh_token(
        req: RefreshTokenRequest,
        repository: Annotated[SysUserRepository, Depends(get_user_repository)],
        token_helper: Annotated[TokenHelper, Depends(get_token_helper)],
        response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)],
):
    try:
        payload = token_helper.decode_token(req.token)
        if payload.get("type") != "refresh_token":
            raise Exception("Invalid refresh token")

        username = payload.get("sub")
        user = repository.get_user(username)

        if not user:
            raise Exception("Invalid refresh token")

        new_access_token = token_helper.create_access_token(user)

        token = BaseToken(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=token_helper.config.jwt_access_token_expire_minutes * 60
        )
        return response_builder.ok(data=token.model_dump())
    except ExpiredSignatureError:
        return response_builder.unauthorized("Refresh token has expired")
    except (InvalidTokenError, DecodeError):
        return response_builder.unauthorized("Invalid refresh token")
    except Exception as e:
        LOGGER.error(f"Error refreshing token: {e}")
        return response_builder.unauthorized("Could not refresh token")


@router.get(
    "/me",
    responses={
        401: {"description": "Unauthorized"},
        400: {"description": "Inactive user"},
    })
async def read_users_me(
        current_user: Annotated[User, Depends(require_role(["payrollprocess"]))],
        response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)],
):
    try:
        return response_builder.ok(data=current_user.model_dump())
    except HTTPException as e:
        LOGGER.error(e)
        if e.status_code == 400:
            return response_builder.bad_request(e.detail)
        else:
            return response_builder.forbidden(e.detail)


@router.options(
    "/validate",
    summary="Validate user credentials",
)
async def validate_token(
        req: Annotated[RefreshTokenRequest, Query()],
        token_helper: Annotated[TokenHelper, Depends(get_token_helper)],
        response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)],
):
    try:
        payload = token_helper.decode_token(req.token)

        content = {
            "valid": True,
            "username": payload.get("sub"),
            "role": payload.get("role"),
            "expires_at": payload.get("exp"),
            "token_type": payload.get("type")
        }
        return response_builder.ok(data=content)
    except ExpiredSignatureError:
        return response_builder.ok({
            "valid": False,
            "error": "Token has expired"
        })
    except (InvalidTokenError, DecodeError):
        return response_builder.ok({
            "valid": False,
            "error": "Invalid token"
        })
    except Exception as e:
        LOGGER.error(f"Error validating token: {e}")
        return response_builder.ok({
            "valid": False,
            "error": "Token validation error"
        })
