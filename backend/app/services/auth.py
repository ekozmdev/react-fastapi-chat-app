"""Authentication-related response helpers."""

from ..core.security import JWT_ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from ..models import User
from ..schemas import UserResponse


def create_token_response(user_id: str) -> dict[str, str | int]:
    """JWTトークンレスポンスを生成"""
    access_token = create_access_token(data={"sub": user_id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def create_user_response(user: User) -> UserResponse:
    """UserResponseを生成"""
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        created_at=user.created_at,
    )
