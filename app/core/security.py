"""
Security module: Token issuance, verification, and auth dependencies.

Split from monolith TokenHelper — TokenIssuer and TokenVerifier are
pure classes with no reference to SysUserRepository. Composition
happens at the router / Depends level.
"""
from datetime import timedelta, datetime, timezone
from typing import Optional, Annotated, Dict, Any

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import ExpiredSignatureError, InvalidTokenError, DecodeError
from starlette import status

from app.core.config import Config, SqidsHelper, LOGGER
from app.models.response_model import User, TokenPayload
from app.repositories.sys_menu import SysMenuRepository, get_sys_menu_repository
from app.repositories.sys_user import SysUserRepository, get_sys_user_repository


# ---------- Token Issuer ----------

class TokenIssuer:
    """Creates signed JWT tokens. No dependency on user repository."""

    def __init__(self, config: Config):
        self.config = config

    def issue_access(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        try:
            now = datetime.now(timezone.utc)
            expire = now + (expires_delta or timedelta(minutes=self.config.jwt_access_token_expire_minutes))

            to_encode = {
                "sub": data.get("username"),
                "name": data.get("full_name"),
                "email": data.get("email"),
                "role": data.get("role"),
                "exp": expire,
                "iat": now,
                "type": "access_token",
            }

            return jwt.encode(
                to_encode,
                self.config.jwt_secret_key,
                algorithm=self.config.jwt_algorithm,
            )
        except Exception as e:
            LOGGER.error(f"Error creating access token: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create access token",
            )

    def issue_refresh(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        try:
            now = datetime.now(timezone.utc)
            expire = now + (expires_delta or timedelta(minutes=self.config.jwt_access_token_expire_minutes))

            to_encode = {
                "sub": data.get("username"),
                "exp": expire,
                "iat": now,
                "type": "refresh_token",
            }

            return jwt.encode(
                to_encode,
                self.config.jwt_secret_key,
                algorithm=self.config.jwt_algorithm,
            )
        except Exception as e:
            LOGGER.error(f"Error creating refresh token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create refresh token",
            )


# ---------- Token Verifier ----------

class TokenVerifier:
    """Decodes and verifies signed JWT tokens. Pure — no side effects."""

    def __init__(self, config: Config):
        self.config = config

    def verify(self, token: str) -> Dict[str, Any]:
        """Decode and verify a JWT. Raises PyJWT exceptions on failure."""
        return jwt.decode(
            token,
            key=self.config.jwt_secret_key,
            algorithms=[self.config.jwt_algorithm],
        )


# ---------- Factory functions for Depends ----------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_token_issuer() -> TokenIssuer:
    return TokenIssuer(Config())


def get_token_verifier() -> TokenVerifier:
    return TokenVerifier(Config())


async def get_current_user_from_token(
    token: Annotated[str, Depends(oauth2_scheme)],
    verifier: Annotated[TokenVerifier, Depends(get_token_verifier)],
    user_repo: Annotated[SysUserRepository, Depends(get_sys_user_repository)],
) -> User:
    """Dependency: decode token → look up user → return User."""
    try:
        payload = verifier.verify(token)
        username: str | None = payload.get("sub")
        token_type: str | None = payload.get("type")

        if username is None or token_type != "access_token":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_data = user_repo.get_user(username)
        if user_data is None or user_data.get("disabled") is True:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return User(**user_data)
    except HTTPException:
        raise
    except Exception:
        raise


def require_role(required_role: list[str]):
    """Dependency factory: require the current user to have a specific role."""

    def role_checker(
        current_user: Annotated[User, Depends(get_current_user_from_token)],
        menu_repository: Annotated[SysMenuRepository, Depends(get_sys_menu_repository)],
    ) -> User:
        if current_user.disabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )
        sqids_helper = SqidsHelper()
        user_role = current_user.role
        user_role = sqids_helper.decode(user_role)
        menus = menu_repository.fetch_menus(user_role)

        if menus[menus["menu_code"].isin(required_role)].empty:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


def require_any_role(required_roles: list):
    """Dependency factory: require any one role from the list."""

    def role_checker(current_user: User = Depends(get_current_user_from_token)) -> User:
        if current_user.disabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user",
            )
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker
