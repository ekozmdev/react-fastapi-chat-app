"""認証関連のPydanticスキーマ"""

from datetime import datetime

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """ログインリクエスト"""

    email: str
    password: str


class Token(BaseModel):
    """JWT認証トークン"""

    access_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int


class UserResponse(BaseModel):
    """ユーザー情報レスポンス"""

    id: str
    email: str
    username: str
    is_active: bool
    created_at: datetime


