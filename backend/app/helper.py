"""
ヘルパー関数
main.pyから分離されたヘルパー関数群
"""

import json
from datetime import UTC, datetime

from agents.stream_events import RunItemStreamEvent
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .core.security import JWT_ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from .models import Conversation, Message, User
from .schemas import UserResponse


def get_user_conversation(
    db: Session, conversation_id: str, user_id: str
) -> Conversation:
    """ユーザーの会話を取得（権限チェック付き）"""
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if not conv:
        raise HTTPException(404, "Conversation not found")
    return conv


def create_token_response(user_id: str) -> dict:
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


def prepare_conversation_and_user_message(
    db: Session, conversation_id: str, user_id: str, message: str
) -> Conversation:
    """会話を準備してユーザーメッセージを保存"""
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
        .first()
    )

    if not conv:
        # 同じIDの会話が他ユーザーに属していないか確認
        conflict_conv = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )
        if conflict_conv:
            raise HTTPException(404, "Conversation not found")

        # 指定のIDが存在しない場合は新規作成
        conv = Conversation(id=conversation_id, user_id=user_id)
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # ユーザーメッセージ保存
    user_msg = Message(conversation_id=conv.id, role="user", content=message)
    db.add(user_msg)
    db.commit()

    return conv


def convert_messages_for_openai_api(messages: list) -> list[dict]:
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
    event: RunItemStreamEvent, active_tools: dict
) -> tuple[str, dict, str] | None:
    """ツール出力のSSEイベントを生成（副作用なし）"""
    raw_item = getattr(event.item, "raw_item", None)
    output = getattr(event.item, "output", None)

    if raw_item is None or output is None:
        return None

    call_id = getattr(raw_item, "call_id", None)
    if call_id is None and isinstance(raw_item, dict):
        call_id = raw_item.get("call_id")
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
        "content": json.dumps(tool_content_dict, ensure_ascii=False),
        "id": call_id,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    db_message_data = {
        "role": "tool",
        "content": json.dumps(tool_content_dict, ensure_ascii=False),
    }

    sse_data = f"data: {json.dumps(tool_event, ensure_ascii=False)}\n\n"
    return (sse_data, db_message_data, call_id)


def create_assistant_content_sse_event(delta: str, assistant_id: str) -> str:
    """アシスタントコンテンツのSSEイベントを生成"""
    content_event = {
        "role": "assistant",
        "content": delta,
        "id": assistant_id,
    }
    return f"data: {json.dumps(content_event, ensure_ascii=False)}\n\n"


def save_message(db: Session, conversation_id: str, role: str, content: str) -> None:
    """1つのメッセージをデータベースに保存"""
    if content.strip():  # 空のコンテンツは保存しない
        db_message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        db.add(db_message)


def finalize_conversation(db: Session, conv: Conversation) -> None:
    """会話を完了処理（タイトル生成・更新日時設定）"""
    # タイトル自動生成
    if not conv.title and len(conv.messages) > 0:
        first_user_msg = next((m for m in conv.messages if m.role == "user"), None)
        if first_user_msg:
            conv.title = first_user_msg.content[:50] + (
                "..." if len(first_user_msg.content) > 50 else ""
            )

    conv.updated_at = datetime.now(UTC)
    db.commit()
