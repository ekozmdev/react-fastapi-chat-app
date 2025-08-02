import json
import uuid
from datetime import UTC, datetime

from agents import Agent, Runner
from agents.stream_events import RawResponsesStreamEvent
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai.types.responses import (
    ResponseFunctionCallArgumentsDeltaEvent,
    ResponseTextDeltaEvent,
)
from sqlalchemy.orm import Session

from .clients import get_chat_agent, lifespan
from .core.config import settings
from .core.deps import get_current_user as get_current_user_dep
from .core.security import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_password_hash,
    verify_password,
)
from .db.session import get_db
from .models import Conversation, Message, User
from .schemas import (
    ChatRequest,
    LoginRequest,
    Token,
    UserResponse,
    UserUpdateRequest,
)

app = FastAPI(title=settings.APP_TITLE, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)





# ---------- Dependency ----------
# get_current_userは core/deps.pyに移動済み
get_current_user = get_current_user_dep


# ---------- 認証エンドポイント ----------
@app.post("/api/auth/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """ユーザーログイン"""
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")

    access_token = create_access_token(data={"sub": user.id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@app.post("/api/auth/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """トークンリフレッシュ"""
    access_token = create_access_token(data={"sub": current_user.id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """現在のユーザー情報を取得"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@app.put("/api/auth/me", response_model=UserResponse)
async def update_user_info(
    update_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """ユーザー情報を更新"""
    # ユーザー名の更新
    if update_data.username is not None:
        # 重複チェック
        existing_user = (
            db.query(User)
            .filter(User.username == update_data.username, User.id != current_user.id)
            .first()
        )
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        current_user.username = update_data.username

    # パスワードの更新
    if update_data.new_password is not None:
        if update_data.current_password is None:
            raise HTTPException(status_code=400, detail="Current password is required")

        if not verify_password(
            update_data.current_password, current_user.password_hash
        ):
            raise HTTPException(status_code=400, detail="Incorrect current password")

        current_user.password_hash = get_password_hash(update_data.new_password)

    current_user.updated_at = datetime.now(UTC)
    db.commit()

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@app.delete("/api/auth/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """ログアウト（クライアント側でトークンを削除）"""
    return {"message": "Successfully logged out"}


# ---------- REST ----------
# 非ストリーミング実装は廃止済み（SSEストリーミングで代替）


@app.post("/api/conversations")
async def create_conversation(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    conv = Conversation(user_id=current_user.id)
    db.add(conv)
    db.commit()
    return {
        "conversation_id": conv.id,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
    }


@app.get("/api/conversations")
async def list_conversations(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return {
        "conversations": [
            {
                "id": c.id,
                "title": c.title,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "message_count": len(c.messages),
            }
            for c in convs
        ]
    }





@app.get("/api/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id, Conversation.user_id == current_user.id
        )
        .first()
    )
    if not conv:
        raise HTTPException(404, "Conversation not found")
    return {
        "conversation": {
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
        },
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "timestamp": m.created_at,
            }
            for m in conv.messages
        ],
    }


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id, Conversation.user_id == current_user.id
        )
        .first()
    )
    if not conv:
        raise HTTPException(404, "Conversation not found")
    db.delete(conv)
    db.commit()
    return {"message": "deleted"}


# ---------- Helper Functions ----------
def should_include_message(message: Message) -> bool:
    """メッセージをAPI履歴に含めるかを判定"""
    if message.role == "tool":
        return False
    if message.role == "assistant":
        try:
            data = json.loads(message.content)
            return "tool_calls" not in data
        except json.JSONDecodeError:
            return True
    return True


# ---------- SSE ----------
@app.post("/api/chat/stream/{conversation_id}")
async def stream_chat(
    conversation_id: str,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    chat_agent: Agent = Depends(get_chat_agent),
):
    """SSEによるリアルタイムチャット"""

    async def generate_sse_stream():
        try:
            # 会話の取得または作成
            conv = (
                db.query(Conversation)
                .filter(
                    Conversation.id == conversation_id,
                    Conversation.user_id == current_user.id,
                )
                .first()
            )

            if not conv:
                conv = Conversation(id=conversation_id, user_id=current_user.id)
                db.add(conv)
                db.commit()


            # userメッセージはストリーミング前に必ず1回だけ保存
            user_msg = Message(
                conversation_id=conv.id, role="user", content=request.message
            )
            db.add(user_msg)
            db.commit()

            # API用メッセージ履歴を準備（toolメッセージは除外）
            api_messages = [
                {"role": m.role, "content": m.content}
                for m in conv.messages 
                if should_include_message(m)
            ]

            # ストリーミング開始
            assistant_content = ""
            assistant_id = str(uuid.uuid4())
            tool_tracking = {}  # ツール実行追跡: call_id -> {tool_name, tool_call_id}
            sent_tool_messages = []  # SSE送信したrole:toolメッセージを保存（DB保存用）

            # Agents SDK でストリーミング実行（依存性注入されたagent使用）
            result = Runner.run_streamed(chat_agent, api_messages)
            async for event in result.stream_events():
                # ツールイベント検出
                if hasattr(event, "item") and hasattr(event.item, "type"):

                    if event.item.type == "tool_call_item":
                        # ツール呼び出し開始
                        raw_item = event.item.raw_item
                        tool_name = (
                            raw_item.get("name")
                            if hasattr(raw_item, "get")
                            else getattr(raw_item, "name", "unknown")
                        )
                        call_id = getattr(event.item, "id", str(uuid.uuid4()))

                        tool_tracking[call_id] = {
                            "tool_name": tool_name,
                            "tool_call_id": call_id
                        }

                    elif event.item.type == "tool_call_output_item":
                        # ツール実行完了
                        # call_idを複数の方法で取得を試行
                        call_id = (
                            getattr(event.item, "tool_call_id", None) or
                            getattr(event.item, "id", None) or
                            getattr(getattr(event.item, "raw_item", {}), "tool_call_id", None) or
                            "unknown_call"
                        )
                        output = getattr(event.item, "output", "")

                        # ツール名を特定（辞書からまたは別の方法で）
                        tool_name = ""
                        tool_info = None

                        # まず辞書から検索
                        if call_id in tool_tracking:
                            tool_info = tool_tracking[call_id]
                            tool_name = tool_info["tool_name"]
                        else:
                            # 辞書にない場合は、最初のエントリを使用（単一ツール実行の場合）
                            if len(tool_tracking) == 1:
                                first_key = next(iter(tool_tracking))
                                tool_info = tool_tracking[first_key]
                                tool_name = tool_info["tool_name"]
                                call_id = first_key  # 正しいIDに修正
                            else:
                                # 部分的なIDマッチングも試行
                                for tid, tinfo in tool_tracking.items():
                                    if tid in call_id or call_id in tid:
                                        tool_info = tinfo
                                        tool_name = tinfo["tool_name"]
                                        call_id = tid  # 正しいIDに修正
                                        break

                        if tool_info:
                            # phase1.md仕様のrole: toolイベントを送信
                            tool_content_dict = {
                                "tool_call_id": call_id,
                                "tool_name": tool_name,
                                "output": output,
                                "status": "success"
                            }

                            tool_event = {
                                "role": "tool",
                                "content": json.dumps(tool_content_dict, ensure_ascii=False),
                                "id": call_id,
                                "timestamp": datetime.now(UTC).isoformat()
                            }
                            yield f"data: {json.dumps(tool_event, ensure_ascii=False)}\n\n"

                            # DB保存用に情報を保存
                            sent_tool_messages.append({
                                "role": "tool",
                                "content": json.dumps(tool_content_dict, ensure_ascii=False)
                            })

                            # 完了したツールは辞書から削除
                            del tool_tracking[call_id]

                # Phase 2: RawResponsesStreamEvent処理（テキストストリーミング）
                elif isinstance(event, RawResponsesStreamEvent):
                    if isinstance(event.data, ResponseTextDeltaEvent):
                        content = event.data.delta
                        assistant_content += content
                        content_event = {
                            "role": "assistant",
                            "content": content,
                            "id": assistant_id
                        }
                        yield f"data: {json.dumps(content_event, ensure_ascii=False)}\n\n"
                    elif isinstance(event.data, ResponseFunctionCallArgumentsDeltaEvent):
                        pass

            # メッセージ保存
            # SSE送信したツールメッセージを保存
            for tool_msg in sent_tool_messages:
                db_message = Message(
                    conversation_id=conv.id,
                    role=tool_msg["role"],
                    content=tool_msg["content"]
                )
                db.add(db_message)

            # 最終的なassistantメッセージを保存（assistant_contentがある場合のみ）
            if assistant_content.strip():
                db_message = Message(
                    conversation_id=conv.id,
                    role="assistant",
                    content=assistant_content
                )
                db.add(db_message)


            # タイトル生成処理
            if not conv.title and len(conv.messages) > 0:
                first_user_msg = next(
                    (m for m in conv.messages if m.role == "user"), None
                )
                if first_user_msg:
                    conv.title = first_user_msg.content[:50] + (
                        "..." if len(first_user_msg.content) > 50 else ""
                    )

            conv.updated_at = datetime.now(UTC)
            db.commit()

            # ストリーミング完了
            done_event = {"id": assistant_id}
            yield f"done: {json.dumps(done_event, ensure_ascii=False)}\n"

        except Exception as e:
            # エラー送信
            error_event = {"error": f"エラーが発生しました: {str(e)}"}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
        finally:
            db.close()

    return StreamingResponse(
        generate_sse_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Authorization",
        },
    )


# ---------- run ----------
def start():
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)  # noqa: S104


if __name__ == "__main__":
    start()
