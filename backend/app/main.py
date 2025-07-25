import os
import time
import uuid
from datetime import UTC, datetime
from typing import Any, Literal

import uvicorn
from agents import Agent, ModelSettings, Runner
from agents.stream_events import RawResponsesStreamEvent
from dotenv import load_dotenv
from openai.types.responses import ResponseTextDeltaEvent, ResponseFunctionCallArgumentsDeltaEvent
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials
from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .auth import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_password_hash,
    security,
    verify_password,
    verify_token,
)
from .database import get_db
from .models import Conversation, Message, User
from .tools import AVAILABLE_TOOLS

load_dotenv()

app = FastAPI(title="LLM Chat API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番は絞る
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Agents SDK設定（Phase 1でツール機能を追加）
chat_agent = Agent(
    name="ChatAssistant",
    instructions="""あなたは親切で知識豊富なアシスタントです。
    ユーザーの質問に正確かつ丁寧に答えてください。
    必要に応じてツールを使用してください。
    時刻の取得や計算が必要な場合は、適切なツールを使用してください。
    回答は常にユーザーの言語で行ってください。""",
    model="gpt-4o",
    model_settings=ModelSettings(
        max_tokens=1024,
        temperature=0.7,
    ),
    tools=AVAILABLE_TOOLS,  # tools.pyで定義されたツールを自動で利用
)


# ---------- Pydantic ----------


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


# Phase 1: ツール実行追跡クラス
class ToolExecutionTracker:
    """ツール実行の追跡とメタデータ生成を管理"""

    def __init__(self):
        self.tools_used: list[dict[str, Any]] = []
        self.current_tool: dict[str, Any] | None = None

    def start_tool(self, tool_name: str, arguments: dict[str, Any]) -> None:
        """ツール実行開始"""
        self.current_tool = {
            "name": tool_name,
            "input": arguments,
            "start_time": time.time() * 1000,  # ミリ秒
            "status": "executing",
        }

    def complete_tool(self, output: str = None, error: str = None) -> None:
        """ツール実行完了"""
        if self.current_tool:
            execution_time = int(time.time() * 1000 - self.current_tool["start_time"])
            self.current_tool.update(
                {
                    "output": output,
                    "error": error,
                    "status": "success" if not error else "error",
                    "execution_time_ms": execution_time,
                }
            )
            self.tools_used.append(self.current_tool)
            self.current_tool = None

    def get_metadata(self) -> dict[str, Any] | None:
        """tool_metadataを生成"""
        if not self.tools_used:
            return None

        success_count = sum(1 for t in self.tools_used if t["status"] == "success")
        error_count = len(self.tools_used) - success_count
        total_time = sum(t["execution_time_ms"] for t in self.tools_used)

        return {
            "tools_used": self.tools_used,
            "summary": {
                "total_tools": len(self.tools_used),
                "total_time_ms": total_time,
                "success_count": success_count,
                "error_count": error_count,
            },
        }


class SSEEvent(BaseModel):
    type: Literal["status", "content", "done", "error", "tool_start", "tool_complete"]
    message: str | None = None
    content: str | None = None
    message_id: str | None = None
    tool_name: str | None = None
    tool_output: str | None = None
    execution_id: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool
    created_at: datetime


class UserUpdateRequest(BaseModel):
    username: str | None = None
    current_password: str | None = None
    new_password: str | None = None


# ---------- Dependency ----------
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """現在のユーザーを取得"""
    user_id = verify_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=401, detail="Invalid authentication credentials"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")

    return user


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
# @app.post("/api/chat")
# async def chat(req: ChatRequest, db: Session = Depends(get_db)):
#     """最初の 1 往復 (非ストリーミング) 用"""
#     if req.conversation_id:
#         conv = db.query(Conversation).get(req.conversation_id)
#         if not conv:
#             raise HTTPException(404, "Conversation not found")
#     else:
#         conv = Conversation()
#         db.add(conv)
#         db.commit()

#     user_msg = Message(conversation_id=conv.id, role="user", content=req.message)
#     db.add(user_msg)
#     db.commit()

#     # --- Call OpenAI ---
#     api_messages = [{"role": m.role, "content": m.content} for m in conv.messages]
#     api_messages.insert(
#         0,
#         {
#             "role": "system",
#             "content": "You are a helpful assistant. Please respond in the same language as the user's input.",
#         },
#     )
#     resp = client.chat.completions.create(
#         model="gpt-4.1", messages=api_messages, max_tokens=1024, temperature=0.7
#     )
#     assistant_msg = Message(
#         conversation_id=conv.id,
#         role="assistant",
#         content=resp.choices[0].message.content,
#     )
#     db.add(assistant_msg)

#     # --- title生成処理 ---
#     if not conv.title:
#         conv.title = req.message[:50] + ("..." if len(req.message) > 50 else "")
#     conv.updated_at = datetime.utcnow()
#     db.commit()

#     return {
#         "conversation_id": conv.id,
#         "message_id": assistant_msg.id,
#         "message": assistant_msg.content,
#     }


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


# ---------- SSE ----------
@app.post("/api/chat/stream/{conversation_id}")
async def stream_chat(
    conversation_id: str,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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

            # ユーザーメッセージを保存
            user_msg = Message(
                conversation_id=conv.id, role="user", content=request.message
            )
            db.add(user_msg)
            db.commit()

            # API用メッセージ履歴を準備（システムメッセージは除外）
            api_messages = [
                {"role": m.role, "content": m.content} for m in conv.messages
            ]

            # ストリーミング開始
            assistant_content = ""
            assistant_id = str(uuid.uuid4())
            tool_tracker = ToolExecutionTracker()  # Phase 1: ツール追跡開始

            # Agents SDK でストリーミング実行
            result = Runner.run_streamed(chat_agent, api_messages)

            async for event in result.stream_events():
                # Phase 1: ツール実行イベントの処理
                if hasattr(event, "item") and hasattr(event.item, "type"):
                    if event.item.type == "tool_call_item":
                        # ツール呼び出し開始
                        # raw_itemから正確な情報を取得
                        raw_item = event.item.raw_item
                        tool_name = (
                            raw_item.get("name")
                            if hasattr(raw_item, "get")
                            else getattr(raw_item, "name", "unknown")
                        )
                        arguments = (
                            raw_item.get("arguments", {})
                            if hasattr(raw_item, "get")
                            else getattr(raw_item, "arguments", {})
                        )
                        call_id = getattr(
                            event.item, "id", f"call_{int(time.time() * 1000)}"
                        )

                        print(
                            f"Tool call started: name={tool_name}, call_id={call_id}, args={arguments}"
                        )

                        tool_tracker.start_tool(tool_name, arguments)

                        # フロントエンドにツール開始イベントを送信
                        tool_start_event = SSEEvent(
                            type="tool_start",
                            message_id=assistant_id,
                            tool_name=tool_name,
                            execution_id=call_id,
                        )
                        print(
                            f"Sending tool_start event: {tool_start_event.model_dump_json()}"
                        )
                        yield f"data: {tool_start_event.model_dump_json()}\n\n"

                    elif event.item.type == "tool_call_output_item":
                        # ツール実行完了
                        output = getattr(event.item, "output", "")
                        error = getattr(event.item, "error", None)
                        call_id = getattr(event.item, "tool_call_id", "unknown_call")

                        # 前回開始したツールの名前を使用
                        tool_name = (
                            tool_tracker.current_tool["name"]
                            if tool_tracker.current_tool
                            else "unknown"
                        )

                        print(
                            f"Tool call completed: call_id={call_id}, output={output}"
                        )

                        tool_tracker.complete_tool(output=output, error=error)

                        # フロントエンドにツール完了イベントを送信
                        tool_complete_event = SSEEvent(
                            type="tool_complete",
                            message_id=assistant_id,
                            tool_name=tool_name,
                            tool_output=output,
                            execution_id=call_id,
                        )
                        print(
                            f"Sending tool_complete event: {tool_complete_event.model_dump_json()}"
                        )
                        yield f"data: {tool_complete_event.model_dump_json()}\n\n"

                elif event.type == "raw_response_event":
                    # RawResponsesStreamEventかどうかをまず確認
                    if isinstance(event, RawResponsesStreamEvent):
                        # 型チェックによる完全分離（フィルタリング不要）
                        if isinstance(event.data, ResponseTextDeltaEvent):
                            content = event.data.delta  # 純粋なAI応答のみ
                            assistant_content += content
                            
                            # コンテンツストリーミング
                            content_event = SSEEvent(
                                type="content", content=content, message_id=assistant_id
                            )
                            yield f"data: {content_event.model_dump_json()}\n\n"
                        elif isinstance(event.data, ResponseFunctionCallArgumentsDeltaEvent):
                            # ツール引数は完全に無視（デバッグ用ログのみ）
                            print(f"Tool arguments ignored: {event.data.delta}")

            # Phase 1: ツールメタデータを含めてアシスタントメッセージを保存
            tool_metadata = tool_tracker.get_metadata()
            db.add(
                Message(
                    id=assistant_id,
                    conversation_id=conv.id,
                    role="assistant",
                    content=assistant_content,
                    tool_metadata=tool_metadata,
                )
            )

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
            done_event = SSEEvent(type="done", message_id=assistant_id)
            yield f"data: {done_event.model_dump_json()}\n\n"

        except Exception as e:
            # エラー送信
            error_event = SSEEvent(
                type="error", message=f"エラーが発生しました: {str(e)}"
            )
            yield f"data: {error_event.model_dump_json()}\n\n"
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
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)  # noqa: S104


if __name__ == "__main__":
    start()
