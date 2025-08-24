import json
import logging
from datetime import UTC, datetime

from agents import Agent, Runner
from agents.stream_events import RawResponsesStreamEvent, RunItemStreamEvent
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai.types.responses import (
    ResponseTextDeltaEvent,
)
from sqlalchemy.orm import Session

from .clients import get_chat_agent, lifespan
from .core.config import settings
from .core.deps import get_current_user as get_current_user_dep
from .core.security import (
    authenticate_user,
    get_password_hash,
    verify_password,
)
from .core.utils import generate_unique_id
from .db.session import get_db
from .helper import (
    convert_messages_for_openai_api,
    create_assistant_content_sse_event,
    create_tool_output_sse_event,
    create_token_response,
    create_user_response,
    extract_tool_call_info,
    finalize_conversation,
    get_user_conversation,
    prepare_conversation_and_user_message,
    save_message,
)
from .models import Conversation, User
from .schemas import (
    ChatRequest,
    LoginRequest,
    Token,
    UserResponse,
)

# Uvicornのロガーを取得
logger = logging.getLogger('uvicorn.error')

app = FastAPI(title=settings.APP_TITLE, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# Dependency
get_current_user = get_current_user_dep


# 認証エンドポイント
@app.post("/api/auth/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    ユーザーログイン認証

    メールアドレスとパスワードでユーザー認証を行い、JWTアクセストークンを発行します。

    ## パラメータ
    - **email**: ログイン用メールアドレス
    - **password**: ログイン用パスワード

    ## レスポンス
    - **access_token**: JWT認証トークン
    - **token_type**: トークン種別（bearer）
    - **expires_in**: トークン有効期限（秒）

    ## エラー
    - **401**: 認証情報が無効またはアカウント無効
    - **422**: リクエストデータ形式エラー
    """
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")

    return create_token_response(user.id)


@app.post("/api/auth/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """
    JWTトークンリフレッシュ

    現在有効なトークンを使用して新しいアクセストークンを発行します。

    ## 認証
    - **Authorization**: Bearer トークンが必要

    ## レスポンス
    - **access_token**: 新しいJWT認証トークン
    - **token_type**: トークン種別（bearer）
    - **expires_in**: トークン有効期限（秒）

    ## エラー
    - **401**: トークンが無効または期限切れ
    """
    return create_token_response(current_user.id)


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    現在のユーザー情報取得

    認証されたユーザーの詳細情報を取得します。

    ## 認証
    - **Authorization**: Bearer トークンが必要

    ## レスポンス
    - **id**: ユーザーID（UUID）
    - **email**: メールアドレス
    - **username**: ユーザー名
    - **is_active**: アカウント有効状態
    - **created_at**: アカウント作成日時

    ## エラー
    - **401**: トークンが無効または期限切れ
    """
    return create_user_response(current_user)




# REST




@app.get("/api/conversations")
async def list_conversations(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    会話一覧取得

    認証されたユーザーの会話一覧を更新日時降順で取得します。

    ## 認証
    - **Authorization**: Bearer トークンが必要

    ## パラメータ
    - **skip**: スキップする件数（デフォルト: 0）
    - **limit**: 取得件数の上限（デフォルト: 20）

    ## レスポンス
    - **conversations**: 会話情報の配列
      - **id**: 会話ID（UUID）
      - **title**: 会話タイトル
      - **created_at**: 作成日時
      - **updated_at**: 更新日時
      - **message_count**: メッセージ数

    ## エラー
    - **401**: トークンが無効または期限切れ
    """
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
    """
    特定会話の詳細取得

    指定された会話IDの会話情報と全メッセージ履歴を取得します。

    ## 認証
    - **Authorization**: Bearer トークンが必要

    ## パラメータ
    - **conversation_id**: 取得する会話のID（UUID）

    ## レスポンス
    - **conversation**: 会話情報
      - **id**: 会話ID（UUID）
      - **title**: 会話タイトル
      - **created_at**: 作成日時
      - **updated_at**: 更新日時
    - **messages**: メッセージ配列
      - **id**: メッセージID（UUID）
      - **role**: メッセージの役割（user/assistant/tool）
      - **content**: メッセージ内容
      - **timestamp**: 作成日時

    ## エラー
    - **404**: 指定された会話が見つからない
    - **401**: トークンが無効または期限切れ
    """
    conv = get_user_conversation(db, conversation_id, current_user.id)
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
    """
    会話削除

    指定された会話とその全メッセージを完全に削除します。

    ## 認証
    - **Authorization**: Bearer トークンが必要

    ## パラメータ
    - **conversation_id**: 削除する会話のID（UUID）

    ## レスポンス
    - **message**: 削除成功メッセージ

    ## エラー
    - **404**: 指定された会話が見つからない
    - **401**: トークンが無効または期限切れ
    """
    conv = get_user_conversation(db, conversation_id, current_user.id)
    db.delete(conv)
    db.commit()
    return {"message": "deleted"}


# SSE
@app.post("/api/chat/stream")
async def stream_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    chat_agent: Agent = Depends(get_chat_agent),
):
    """
    SSEストリーミングによるリアルタイムチャット

    Server-Sent Events (SSE) を使用してリアルタイムでAIチャット応答をストリーミング配信します。
    OpenAI Agents SDKによるツール実行もサポートし、ツール呼び出しの状況も即座に通知されます。

    ## 認証
    - **Authorization**: Bearer トークンが必要

    ## パラメータ
    - **conversation_id**: チャット会話のID（UUID、存在しない場合は自動作成）
    - **message**: ユーザーからのメッセージ内容

    ## レスポンス形式 (SSE)
    - **data:**: JSON形式のストリーミングデータ
      - `role: "assistant"`: AI応答テキスト（逐次送信）
      - `role: "tool"`: ツール実行結果（完了時送信）
    - **done:**: ストリーミング完了通知

    ## 利用可能ツール
    - **get_current_time**: 現在時刻取得
    - **calculate**: 数学計算実行
    - **web_search**: Web検索実行

    ## エラー
    - **401**: トークンが無効または期限切れ
    - **422**: リクエストデータ形式エラー
    """

    async def generate_sse_stream():
        try:
            # conversation_idの取得・生成
            conversation_id = request.conversation_id
            is_new_conversation = False
            if not conversation_id:  # 空文字の場合
                conversation_id = generate_unique_id()
                is_new_conversation = True
            
            # 新規作成通知をSSEで送信
            if is_new_conversation:
                conversation_info = {
                    "type": "conversation_created",
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now(UTC).isoformat()
                }
                yield f"data: {json.dumps(conversation_info, ensure_ascii=False)}\n\n"
            
            # 1. 会話準備とユーザーメッセージ保存
            conv = prepare_conversation_and_user_message(
                db, conversation_id, current_user.id, request.message
            )

            # 2. API用メッセージ変換
            api_messages = convert_messages_for_openai_api(conv.messages)

            # 3. ストリーミング準備
            assistant_content = ""
            assistant_id = generate_unique_id()
            active_tools = {}
            sent_tool_messages = []

            # 4. Agent実行とイベント処理
            result = Runner.run_streamed(chat_agent, api_messages)
            async for event in result.stream_events():
                logger.debug(f"Stream Event: {event}")
                if isinstance(event, RunItemStreamEvent):
                    if event.name == "tool_called":
                        # ツール呼び出し情報を抽出してactive_toolsに保存
                        tool_info = extract_tool_call_info(event)
                        if tool_info:
                            call_id, tool_name = tool_info
                            active_tools[call_id] = tool_name

                    elif event.name == "tool_output":
                        # ツール出力を処理（純粋関数）
                        tool_response = create_tool_output_sse_event(
                            event, active_tools
                        )
                        if tool_response:
                            sse_event, db_message, call_id = tool_response
                            yield sse_event
                            sent_tool_messages.append(db_message)
                            # 完了したツールをactive_toolsから削除
                            active_tools.pop(call_id, None)

                elif isinstance(event, RawResponsesStreamEvent):
                    if isinstance(event.data, ResponseTextDeltaEvent):
                        delta = event.data.delta
                        assistant_content += delta
                        yield create_assistant_content_sse_event(delta, assistant_id)

            # 5. データベース保存
            # ツールメッセージを保存
            for tool_msg in sent_tool_messages:
                save_message(db, conv.id, tool_msg["role"], tool_msg["content"])

            # アシスタントメッセージを保存
            save_message(db, conv.id, "assistant", assistant_content)

            # 6. 会話完了処理
            finalize_conversation(db, conv)

            # ストリーミング完了
            done_event = {"id": assistant_id}
            yield f"event: done\ndata: {json.dumps(done_event, ensure_ascii=False)}\n\n"

        except Exception as e:
            # エラー送信
            error_event = {"error": f"エラーが発生しました: {str(e)}"}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
        finally:
            db.close()

    return StreamingResponse(
        generate_sse_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Authorization",
        },
    )


# Run
def start():
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)  # noqa: S104


if __name__ == "__main__":
    start()
