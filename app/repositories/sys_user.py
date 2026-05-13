from typing import Optional, Dict, Any

from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status

from app.core.config import Config, SqidsHelper, LOGGER
from app.core.databases import DatabaseHelper

INCORRECT_USERNAME_OR_PASSWORD = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                               detail="Incorrect username or password")


class SysUserRepository:
    """Repository for system user operations (auth, lookup, password check).
    
    Pure database access — no JWT, no token logic.
    """

    def __init__(self):
        self.config = Config()
        self.db_helper = DatabaseHelper()
        self.sqids_helper = SqidsHelper()

    def authenticate(self, auth_request: OAuth2PasswordRequestForm):
        result = self.get_user(auth_request.username)
        if not result:
            raise INCORRECT_USERNAME_OR_PASSWORD
        self.validate_password(auth_request.password, result['user_password'])
        return result

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
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
        params = (str(username),)
        try:
            user_data = self.db_helper.fetchone(query, params)
            if not user_data:
                return None

            if 'role' in user_data and user_data['role'] is not None:
                user_data['role'] = self.sqids_helper.encode(user_data['role'])
            else:
                user_data['role'] = ''
            return user_data
        except Exception as e:
            LOGGER.error(f"Error fetching user: {e}")
            return None

    def validate_password(self, plain_password: str, hashed_password: str):
        query = "SELECT PASSWORD(%s) AS user_password"
        params = (plain_password,)
        result = self.db_helper.fetchone(query, params)
        if not result:
            raise INCORRECT_USERNAME_OR_PASSWORD
        stored_hashed_password = result['user_password']
        if stored_hashed_password != hashed_password:
            raise INCORRECT_USERNAME_OR_PASSWORD


def get_sys_user_repository() -> SysUserRepository:
    """Factory function for Depends injection."""
    return SysUserRepository()
