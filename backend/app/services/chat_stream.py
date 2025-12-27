"""Chat streaming helpers."""

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterable

from agents.stream_events import RunItemStreamEvent

from ..models import Message


@dataclass(frozen=True)
class ToolOutputEvent:
    """ツール出力のSSEイベントとDB保存用データをまとめる"""

    sse_event: str
    db_message: dict[str, str]
    call_id: str


def convert_messages_for_openai_api(messages: Iterable[Message]) -> list[dict[str, str]]:
    """メッセージをOpenAI API用形式に変換"""
    api_messages = []
    for m in messages:
        if m.role == "tool":
            api_messages.append(
                {"role": "assistant", "content": f"ツール実行結果: {m.content}"}
            )
        else:
            api_messages.append({"role": m.role, "content": m.content})
    return api_messages


def extract_tool_call_info(event: RunItemStreamEvent) -> tuple[str, str] | None:
    """ツール呼び出し情報を抽出（副作用なし）"""
    try:
        call_id = event.item.raw_item.call_id
        tool_name = event.item.raw_item.name
        return (call_id, tool_name)
    except (AttributeError, KeyError):
        return None


def create_tool_output_sse_event(
    event: RunItemStreamEvent, active_tools: dict[str, str]
) -> ToolOutputEvent | None:
    """ツール出力のSSEイベントを生成（副作用なし）"""
    raw_item = getattr(event.item, "raw_item", None)
    output = getattr(event.item, "output", None)

    if raw_item is None or output is None:
        return None

    call_id = _resolve_call_id(raw_item)
    if call_id is None:
        return None

    tool_name = active_tools.get(call_id, "unknown")

    tool_content_dict = {
        "tool_call_id": call_id,
        "tool_name": tool_name,
        "output": output,
        "status": "success",
    }

    tool_event = {
        "role": "tool",
        "content": _json_dumps(tool_content_dict),
        "id": call_id,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    db_message_data = {
        "role": "tool",
        "content": _json_dumps(tool_content_dict),
    }

    sse_data = f"data: {_json_dumps(tool_event)}\n\n"
    return ToolOutputEvent(sse_event=sse_data, db_message=db_message_data, call_id=call_id)


def create_assistant_content_sse_event(delta: str, assistant_id: str) -> str:
    """アシスタントコンテンツのSSEイベントを生成"""
    content_event = {
        "role": "assistant",
        "content": delta,
        "id": assistant_id,
    }
    return f"data: {_json_dumps(content_event)}\n\n"


def _resolve_call_id(raw_item: object) -> str | None:
    """tool call idを抽出"""
    call_id = getattr(raw_item, "call_id", None)
    if call_id is None and isinstance(raw_item, dict):
        call_id = raw_item.get("call_id")
    return call_id


def _json_dumps(payload: dict) -> str:
    """JSONシリアライズ（日本語を保持）"""
    return json.dumps(payload, ensure_ascii=False)
