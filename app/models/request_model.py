from typing import Optional

from pydantic import BaseModel


class PaginationQuery(BaseModel):
    page: int = 1
    size: int = 10


class TunkinRequest(PaginationQuery):
    nipam: Optional[str] = None


"""
JWT Model
"""


class AuthRequest(BaseModel):
    username: str
    password: str


class BaseToken(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class Token(BaseToken):
    refresh_token: str


class TokenPayload(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDb(User):
    hashed_password: str

class RefreshTokenRequest(BaseModel):
    token: str