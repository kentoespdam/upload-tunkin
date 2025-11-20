from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from jwt import ExpiredSignatureError, InvalidTokenError, DecodeError
from starlette import status

from app.core.config import Config, LOGGER
from app.models.request_model import User, Token, BaseToken, RefreshTokenRequest
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


# def get_current_active_user(
#         current_user: Annotated[User, Depends(get_token_helper().get_current_user)],
# ) -> User:
#     if current_user['disabled']:
#         raise HTTPException(status_code=400, detail="Inactive user")
#     return current_user


@router.post("/token", summary="Authenticate User and Get Tokens", response_model=Token)
def authenticate_user(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        repository: Annotated[SysUserRepository, Depends(get_user_repository)],
        token_helper: Annotated[TokenHelper, Depends(get_token_helper)],
        config: Annotated[Config, Depends(get_config)],
):
    if not token_helper.validata_client(form_data.client_id, form_data.client_secret):
        raise HTTPException(
            status_code=status.HTTP_401_BAD_REQUEST,
            detail="Invalid client credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = repository.authenticate(form_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if user.get("disabled", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    try:
        access_token = token_helper.create_access_token(
            user,
            timedelta(minutes=config.jwt_access_token_expire_minutes)
        )
        refresh_token = token_helper.create_refresh_token(
            user,
            timedelta(days=7)
        )
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=token_helper.config.jwt_access_token_expire_minutes * 60
        )
    except Exception as e:
        LOGGER.error(f"Error creating tokens: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create tokens"
        )


@router.post(
    "/refresh",
    summary="Refresh Access Token",
    response_model=BaseToken,
    responses={
        401: {"description": "Invalid or expired refresh token"},
    }
)
async def refresh_token(
        req: RefreshTokenRequest,
        repository: Annotated[SysUserRepository, Depends(get_user_repository)],
        token_helper: Annotated[TokenHelper, Depends(get_token_helper)],
):
    try:
        payload = token_helper.decode_token(req.token)
        if payload.get("type") != "refresh_token":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        username = payload.get("sub")
        user = repository.get_user(username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        new_access_token = token_helper.create_access_token(user)

        return BaseToken(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=token_helper.config.jwt_access_token_expire_minutes * 60
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )
    except (InvalidTokenError, DecodeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.get(
    "/me",
    response_model=User,
    responses={
        401: {"description": "Unauthorized"},
        400: {"description": "Inactive user"},
    })
async def read_users_me(
        current_user: Annotated[User, Depends(require_role(["payrollprocess"]))]
):
    return current_user


@router.post(
    "/validate",
    summary="Validate user credentials",
)
async def validate_token(
        token: str,
        token_helper: Annotated[TokenHelper, Depends(get_token_helper)],
):
    try:
        payload = token_helper.decode_token(token)

        return {
            "valid": True,
            "username": payload.get("sub"),
            "role": payload.get("role"),
            "expires_at": payload.get("exp"),
            "token_type": payload.get("type")
        }
    except ExpiredSignatureError:
        return {
            "valid": False,
            "error": "Token has expired"
        }
    except (InvalidTokenError, DecodeError):
        return {
            "valid": False,
            "error": "Invalid token"
        }
    except Exception as e:
        return {
            "valid": False,
            "error": "Token validation error"
        }
