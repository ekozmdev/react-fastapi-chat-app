"""共通Pydanticスキーマ"""

from typing import Literal

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """チャットリクエスト"""

    message: str
    conversation_id: str | None = None


class SSEEvent(BaseModel):
    """Server-Sent Eventデータ"""

    type: Literal[
        "status",
        "content",
        "done",
        "error",
        "tool_start",
        "tool_complete",
        "tool_decision",
    ]
    message: str | None = None
    content: str | None = None
    message_id: str | None = None
    tool_name: str | None = None
    tool_output: str | None = None
    execution_id: str | None = None
