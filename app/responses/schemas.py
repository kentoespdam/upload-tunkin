from datetime import datetime
from typing import Any, Dict, Hashable, List, Optional, Union

from pydantic import BaseModel


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


class BaseResponse(BaseModel):
    status: int
    data: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None
    errors: Optional[Union[str, List[str]]] = None
    message: Optional[str] = None
    timestamp: str = None
    request_id: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BasePageResponse(BaseModel):
    content: List[Dict[Union[str, Hashable], Any]]
    total: int
    is_first: bool
    is_last: bool
    page: int
    page_size: int
    total_pages: int


class PageResponse(BaseResponse):
    data: BasePageResponse


class TunkinModel(BaseModel):
    id: str
    periode: str
    nipam: str
    nama: str
    jabatan: str
    organisasi: str
    status_pegawai: str
    tunkin: int
    ter: int
