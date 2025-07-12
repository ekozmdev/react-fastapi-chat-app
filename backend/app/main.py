import json
import os
import uuid
from datetime import datetime

import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, create_engine
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


# ---------- DB Models ----------
class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
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
    created_at = Column(DateTime, default=datetime.utcnow)
    conversation = relationship("Conversation", back_populates="messages")


Base.metadata.create_all(bind=engine)



# ---------- Pydantic ----------
from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


# ---------- Dependency ----------
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



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
async def create_conversation(db: Session = Depends(get_db)):
    conv = Conversation()
    db.add(conv)
    db.commit()
    return {
        "conversation_id": conv.id,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
    }


@app.get("/api/conversations")
async def list_conversations(
    skip: int = 0, limit: int = 20, db: Session = Depends(get_db)
):
    convs = (
        db.query(Conversation)
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
async def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    conv = db.query(Conversation).get(conversation_id)
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
async def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    conv = db.query(Conversation).get(conversation_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    db.delete(conv)
    db.commit()
    return {"message": "deleted"}


# ---------- WebSocket ----------
@app.websocket("/ws/{conversation_id}")
async def ws_endpoint(ws: WebSocket, conversation_id: str):
    await ws.accept()
    db = SessionLocal()
    try:
        conv = db.query(Conversation).get(conversation_id) or Conversation(
            id=conversation_id
        )
        db.add(conv)
        db.commit()

        while True:
            data = json.loads(await ws.receive_text())
            user_msg = Message(
                conversation_id=conv.id, role="user", content=data["message"]
            )
            db.add(user_msg)
            db.commit()

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

            assistant_content = ""
            assistant_id = str(uuid.uuid4())
            await ws.send_json({"type": "start", "message_id": assistant_id})

            stream = await client.chat.completions.create(
                model="gpt-4.1",
                messages=api_messages,
                max_tokens=1024,
                temperature=0.7,
                stream=True,
            )
            async for ch in stream:
                if ch.choices[0].delta.content:
                    chunk = ch.choices[0].delta.content
                    assistant_content += chunk
                    await ws.send_json(
                        {"type": "stream", "content": chunk, "message_id": assistant_id}
                    )


            db.add(
                Message(
                    id=assistant_id,
                    conversation_id=conv.id,
                    role="assistant",
                    content=assistant_content,
                )
            )

            # --- title生成処理（WebSocket用）---
            if not conv.title and len(conv.messages) > 0:
                # 最初のuserメッセージをタイトルに使う
                first_user_msg = next((m for m in conv.messages if m.role == "user"), None)
                if first_user_msg:
                    conv.title = first_user_msg.content[:50] + ("..." if len(first_user_msg.content) > 50 else "")
            conv.updated_at = datetime.utcnow()
            db.commit()
            await ws.send_json({"type": "end", "message_id": assistant_id})

    except WebSocketDisconnect:
        print("WS disconnect", conversation_id)
    finally:
        db.close()


# ---------- run ----------
def start():
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start()
