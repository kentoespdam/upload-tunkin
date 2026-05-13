from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status

from app.core.config import Config, LOGGER
from app.core.security import (
    get_token_issuer, get_token_verifier, get_current_user_from_token,
    TokenIssuer, TokenVerifier,
)
from app.responses.builder import ResponseBuilder, get_response_builder
from app.responses.schemas import BaseToken, RefreshTokenRequest, Token, User
from app.auth.repository import SysUserRepository, get_sys_user_repository


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


@router.get(
    "/me",
    responses={401: {"description": "Unauthorized"}, 400: {"description": "Inactive user"}},
)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user_from_token)],
    response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)],
):
    return response_builder.ok(data=current_user.model_dump())


def _validate_token_payload(token: str, verifier: TokenVerifier) -> dict:
    """Verify a JWT token and return validation content dict.
    
    This helper captures JWT-level exceptions and maps them to
    the token-validator response format (always 200 with valid flag).
    """
    from jwt import ExpiredSignatureError, InvalidTokenError, DecodeError
    try:
        payload = verifier.verify(token)
        return {
            "valid": True,
            "username": payload.get("sub"),
            "role": payload.get("role"),
            "expires_at": payload.get("exp"),
            "token_type": payload.get("type"),
        }
    except ExpiredSignatureError:
        return {"valid": False, "error": "Token has expired"}
    except (InvalidTokenError, DecodeError):
        return {"valid": False, "error": "Invalid token"}
    except Exception as e:
        LOGGER.error(f"Error validating token: {e}")
        return {"valid": False, "error": "Token validation error"}


@router.options("/validate", summary="Validate token")
async def validate_token(
    req: Annotated[RefreshTokenRequest, Query()],
    verifier: Annotated[TokenVerifier, Depends(get_token_verifier)],
    response_builder: Annotated[ResponseBuilder, Depends(get_response_builder)],
):
    content = _validate_token_payload(req.token, verifier)
    return response_builder.ok(data=content)