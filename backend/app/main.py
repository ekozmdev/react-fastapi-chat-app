import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from openai import AsyncOpenAI
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker

load_dotenv()

app = FastAPI(title="LLM Chat API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番は絞る
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://chatuser:chatpassword@localhost:5432/chatdb"
)
# psycopg3 (psycopg) uses 'postgresql+psycopg' dialect
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# JWT設定
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# パスワードハッシュ化（bcrypt使用）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT認証
security = HTTPBearer()


# ---------- DB Models ----------
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # リレーション
    conversations = relationship("Conversation", back_populates="user")


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # リレーション
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        order_by="Message.created_at",
        cascade="all, delete-orphan",
    )


class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    conversation = relationship("Conversation", back_populates="messages")


# Base.metadata.create_all(bind=engine)  # Alembicでマイグレーション管理するため無効化


# ---------- 認証ヘルパー関数 ----------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワードを検証"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """パスワードをハッシュ化"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """JWTアクセストークンを作成"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> str | None:
    """JWTトークンを検証してuser_idを返す"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """ユーザー認証"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user



# ---------- Pydantic ----------


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class SSEEvent(BaseModel):
    type: Literal["status", "content", "done", "error"]
    message: str | None = None
    content: str | None = None
    message_id: str | None = None
    tool_name: str | None = None
    step: str | None = None


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
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """現在のユーザーを取得"""
    user_id = verify_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

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
        "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@app.post("/api/auth/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """トークンリフレッシュ"""
    access_token = create_access_token(data={"sub": current_user.id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """現在のユーザー情報を取得"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@app.put("/api/auth/me", response_model=UserResponse)
async def update_user_info(
    update_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """ユーザー情報を更新"""
    # ユーザー名の更新
    if update_data.username is not None:
        # 重複チェック
        existing_user = db.query(User).filter(
            User.username == update_data.username,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        current_user.username = update_data.username

    # パスワードの更新
    if update_data.new_password is not None:
        if update_data.current_password is None:
            raise HTTPException(status_code=400, detail="Current password is required")

        if not verify_password(update_data.current_password, current_user.password_hash):
            raise HTTPException(status_code=400, detail="Incorrect current password")

        current_user.password_hash = get_password_hash(update_data.new_password)

    current_user.updated_at = datetime.now(UTC)
    db.commit()

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        created_at=current_user.created_at
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
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
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
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
    db: Session = Depends(get_db)
):
    """SSEによるリアルタイムチャット"""

    async def generate_sse_stream():
        try:
            # 会話の取得または作成
            conv = db.query(Conversation).filter(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id
            ).first()

            if not conv:
                conv = Conversation(id=conversation_id, user_id=current_user.id)
                db.add(conv)
                db.commit()

            # ユーザーメッセージを保存
            user_msg = Message(
                conversation_id=conv.id,
                role="user",
                content=request.message
            )
            db.add(user_msg)
            db.commit()

            # API用メッセージ履歴を準備
            api_messages = [
                {"role": m.role, "content": m.content} for m in conv.messages
            ]
            api_messages.insert(
                0,
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Please respond in the same language as the user's input.",
                },
            )

            # ストリーミング開始
            assistant_content = ""
            assistant_id = str(uuid.uuid4())


            # OpenAI ストリーミング開始
            stream = await client.chat.completions.create(
                model="gpt-4.1",
                messages=api_messages,
                max_tokens=1024,
                temperature=0.7,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    assistant_content += content

                    # コンテンツストリーミング
                    content_event = SSEEvent(
                        type="content",
                        content=content,
                        message_id=assistant_id
                    )
                    yield f"data: {content_event.model_dump_json()}\n\n"

            # アシスタントメッセージを保存
            db.add(
                Message(
                    id=assistant_id,
                    conversation_id=conv.id,
                    role="assistant",
                    content=assistant_content,
                )
            )

            # タイトル生成処理
            if not conv.title and len(conv.messages) > 0:
                first_user_msg = next((m for m in conv.messages if m.role == "user"), None)
                if first_user_msg:
                    conv.title = first_user_msg.content[:50] + ("..." if len(first_user_msg.content) > 50 else "")

            conv.updated_at = datetime.now(UTC)
            db.commit()

            # ストリーミング完了
            done_event = SSEEvent(
                type="done",
                message_id=assistant_id
            )
            yield f"data: {done_event.model_dump_json()}\n\n"

        except Exception as e:
            # エラー送信
            error_event = SSEEvent(
                type="error",
                message=f"エラーが発生しました: {str(e)}"
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
        }
    )


# ---------- run ----------
def start():
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)  # noqa: S104


if __name__ == "__main__":
    start()
