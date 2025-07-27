"""会話関連のPydanticスキーマ"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ConversationResponse(BaseModel):
    """会話レスポンス"""
    id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    message_count: int | None = None


class MessageResponse(BaseModel):
    """メッセージレスポンス"""
    id: str
    role: str
    content: str
    timestamp: datetime
    toolExecutions: list[dict[str, Any]] | None = None