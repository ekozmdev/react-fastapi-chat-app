"""Conversation persistence helpers."""

from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import Conversation, Message


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
    if not conv.title and conv.messages:
        title = _build_conversation_title(conv.messages)
        if title:
            conv.title = title

    conv.updated_at = datetime.now(UTC)
    db.commit()


def _build_conversation_title(messages: list[Message]) -> str | None:
    """会話タイトルを生成"""
    if not messages:
        return None

    first_user_msg = next((m for m in messages if m.role == "user"), None)
    if not first_user_msg:
        return None

    content = first_user_msg.content
    return content[:50] + ("..." if len(content) > 50 else "")
