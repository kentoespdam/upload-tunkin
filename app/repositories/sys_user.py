from datetime import timedelta, datetime
from typing import Optional, Annotated, Dict, Any

import jwt
import pytz
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jwt import InvalidTokenError, ExpiredSignatureError, DecodeError
from starlette import status

from app.core.config import Config, SqidsHelper, LOGGER
from app.core.databases import DatabaseHelper
from app.models.request_model import TokenPayload
from app.repositories.sys_menu import SysMenuRepository, get_sys_menu_repository


class SysUserRepository:
    def __init__(self):
        self.config = Config()
        self.db_helper = DatabaseHelper()
        self.sqids_helper = SqidsHelper()

    def authenticate(self, auth_request: OAuth2PasswordRequestForm):
        try:
            result = self.get_user(auth_request.username)
            if not result:
                return None
            if not self.validate_password(auth_request.password, result['user_password']):
                return None
            return result
        except Exception as e:
            LOGGER.error(f"Authentication error: {e}")
            return None

    def get_user(self, username: str):
        query = f"""
            SELECT
                su.user_login AS username,
                ep.emp_name AS full_name,
                ep.emp_email AS email,
                IF(em.emp_status =1, FALSE, TRUE) AS disabled,
                su.user_role_id AS role,
                su.user_password AS user_password
            FROM
                sys_user AS su
                INNER JOIN employee AS em ON su.user_emp_id = em.emp_id
	            INNER JOIN emp_profile AS ep ON em.emp_profile_id= ep.emp_profile_id
            WHERE
                su.user_login = %s
        """
        params = (username,)
        try:
            result = self.db_helper.fetch_data(query, params)
            if result.empty:
                return None

            user_data = result.to_dict(orient="records")[0]
            if 'role' in user_data and user_data['role'] is not None:
                user_data['role'] = self.sqids_helper.encode(user_data['role'])
            else:
                user_data['role'] = ''
            return user_data
        except Exception as e:
            LOGGER.error(f"Error fetching user: {e}")
            return None

    def validate_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            query = "SELECT PASSWORD(%s) AS user_password"
            params = (plain_password,)
            result = self.db_helper.fetch_tuple_data(query, params, fetchone=True)
            if not result:
                return False
            stored_hashed_password = result['user_password']
            return stored_hashed_password == hashed_password
        except Exception as e:
            LOGGER.error(f"Password validation error: {e}")
            return False


"""
JWT Token Helper
"""
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class TokenHelper:
    def __init__(self):
        self.config = Config()
        self.repository = SysUserRepository()
        self.timezone = pytz.timezone('Asia/Jakarta')

    def validata_client(self, client_id: str, client_secret: str) -> Optional[bool]:
        try:
            if (self.config.jwt_client_id == client_id and
                    self.config.jwt_client_secret == client_secret):
                return True
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,

            )

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        try:
            now = datetime.now(self.timezone)
            expire = now + (expires_delta or timedelta(minutes=self.config.jwt_access_token_expire_minutes))

            to_encode = {
                "sub": data['username'],
                "name": data["full_name"],
                "email": data["email"],
                "role": data["role"],
                "exp": expire,
                "iat": now,
                "type": "access_token"
            }

            encoded_jwt = jwt.encode(
                to_encode,
                self.config.jwt_secret_key,
                algorithm=self.config.jwt_algorithm
            )
            return encoded_jwt
        except Exception as e:
            LOGGER.error(f"Error creating access token: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create access token"
            )

    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        try:
            now = datetime.now(self.timezone)
            expire = now + (expires_delta or timedelta(minutes=self.config.jwt_access_token_expire_minutes))

            to_encode = {
                "sub": data['username'],
                "exp": expire,
                "iat": now,
                "type": "refresh_token"
            }

            encoded_jwt = jwt.encode(
                to_encode,
                self.config.jwt_secret_key,
                algorithm=self.config.jwt_algorithm
            )
            return encoded_jwt
        except Exception as e:
            LOGGER.error(f"Error creating refresh token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not create refresh token"
            )

    async def get_current_user(self, token: Annotated[str, Depends(oauth2_scheme)]) -> Dict[str, Any]:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = self.decode_token(token)
            username = payload.get("sub")
            token_type: str = payload.get("type")

            if username is None or token_type != "access_token":
                raise credentials_exception

            token_data = TokenPayload(username=username)
            user = self.repository.get_user(token_data.username)

            if user is None or user.get('disabled', True):
                raise credentials_exception
            return user
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except (InvalidTokenError, DecodeError):
            raise credentials_exception
        except Exception as e:
            LOGGER.error(f"Get current user error: {e}")
            raise credentials_exception

    def decode_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                key=self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm]
            )
            return payload
        except ExpiredSignatureError as e:
            LOGGER.error(f"Token expired: {e}")
            raise
        except (InvalidTokenError, DecodeError) as e:
            LOGGER.error(f"Invalid token error: {e}")
            raise
        except Exception as e:
            print(f"Token decode error: {e}")
            raise InvalidTokenError("Invalid token")

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = self.decode_token(token)
            return payload
        except Exception as e:
            LOGGER.error(f"Error Verify token: {e}")
            return None


def require_role(required_role: list[str]):
    def role_checker(
            current_user: Annotated[Dict[str, Any], Depends(TokenHelper().get_current_user)],
            menu_repository: Annotated[SysMenuRepository, Depends(get_sys_menu_repository)]
    ):
        if current_user["disabled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        sqids_helper = SqidsHelper()
        user_role = current_user.get('role')
        user_role = sqids_helper.decode(user_role)
        menus= menu_repository.fetch_menus(user_role)

        if menus[menus['menu_code'].isin(required_role)].empty:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user

    return role_checker


def require_any_role(required_roles: list):
    """Decorator for multiple role-based authorization"""

    def role_checker(current_user: Dict[str, Any] = Depends(TokenHelper().get_current_user)):
        if current_user["disabled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        if current_user.get('role') not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user

    return role_checker
