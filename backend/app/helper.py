"""Backward-compatible helpers (deprecated)."""

from .services.auth import create_token_response, create_user_response
from .services.chat_stream import (
    convert_messages_for_openai_api,
    create_assistant_content_sse_event,
    create_tool_output_sse_event,
    extract_tool_call_info,
)
from .services.conversations import (
    finalize_conversation,
    get_user_conversation,
    prepare_conversation_and_user_message,
    save_message,
)

__all__ = [
    "convert_messages_for_openai_api",
    "create_assistant_content_sse_event",
    "create_token_response",
    "create_tool_output_sse_event",
    "create_user_response",
    "extract_tool_call_info",
    "finalize_conversation",
    "get_user_conversation",
    "prepare_conversation_and_user_message",
    "save_message",
]
