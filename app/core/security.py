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
from starlette import status

from app.auth.menu_lookup import DBMenuLookup
from app.auth.permission_checker import PermissionChecker
from app.core.config import Config, SqidsHelper, LOGGER
from app.core.databases import DatabaseHelper
from app.models.response_model import User
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


def get_db_menu_lookup() -> DBMenuLookup:
    return DBMenuLookup(DatabaseHelper())


def get_permission_checker(
    menu_lookup: Annotated[DBMenuLookup, Depends(get_db_menu_lookup)],
) -> PermissionChecker:
    return PermissionChecker(menu_lookup)


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


def require_role(required_menu_codes: list[str]):
    """Dependency factory: require the current user to have at least one of the menu codes."""

    def role_checker(
        current_user: Annotated[User, Depends(get_current_user_from_token)],
        permission_checker: Annotated[PermissionChecker, Depends(get_permission_checker)],
    ) -> User:
        sqids_helper = SqidsHelper()
        role_id = sqids_helper.decode(current_user.role)

        if not permission_checker.allows(role_id, required_menu_codes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker


def require_any_role(required_roles: list):
    """Dependency factory: require the user's role string to match one of the given values."""

    def role_checker(current_user: User = Depends(get_current_user_from_token)) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker
