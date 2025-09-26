# React FastAPI Chat App API仕様書
- ドキュメントバージョン: 0.1
- 最終更新日: 2025-09-26
- 対象サービス: `backend/app`

## 1. 概要
このドキュメントは本アプリケーション（React + FastAPI製チャットアプリ）のバックエンドが提供するHTTP APIおよびSSEインターフェースをリバースエンジニアリングにより整理したものです。主な利用者はフロントエンド開発者、運用チーム、および外部連携を検討するエンジニアを想定しています。

## 2. 共通仕様
### 2.1 ベースURL
- 開発環境（`uvicorn`デフォルト）: `http://localhost:8000`
- すべてのRESTエンドポイントは `/api` プレフィックス配下に配置されています。

### 2.2 認証
- 認証方式: JWT Bearer Token
- 認証ヘッダー: `Authorization: Bearer <access_token>`
- トークン取得: `/api/auth/login`
- トークン有効期限: 環境変数 `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`。未設定時はデフォルトで 1440 分（24 時間）。レスポンスでは秒 (`expires_in`) で返却されます。

### 2.3 CORS
- 許可オリジン: 環境変数 `CORS_ORIGINS` で制御（デフォルトは `http://localhost:3000` および `http://localhost:80`）。
- 許可メソッド: `GET, POST, PUT, DELETE`
- 認証情報送信: 許可 (`Access-Control-Allow-Credentials: true`)
- 許可ヘッダー: `*`

### 2.4 エラーレスポンス共通仕様
- スキーマ: `{"detail": string}`（FastAPI標準）。
- バリデーションエラー時は `422 Unprocessable Entity` でPydanticの詳細が返却されます。

## 3. ドメインモデル概要
| モデル | 主なフィールド | 説明 |
| --- | --- | --- |
| User | `id`, `email`, `username`, `is_active`, `created_at` | 認可済みユーザー。`username` と `email` はユニーク制約あり。|
| Conversation | `id`, `user_id`, `title`, `created_at`, `updated_at` | ユーザーごとの会話スレッド。`title` は最初のユーザーメッセージから自動生成される場合がある。|
| Message | `id`, `conversation_id`, `role`(`user`/`assistant`/`tool`), `content`, `created_at` | 会話に紐づくメッセージ履歴。SSE配信後にDBへ保存される。|

## 4. エンドポイント詳細
### 4.1 認証 API
#### POST `/api/auth/login`
- 概要: メールアドレスとパスワードでログインし、JWTアクセストークンを発行します。
- 認証: 不要
- リクエストボディ:
  ```json
  {
    "email": "user@example.com",
    "password": "plain-text"
  }
  ```
- レスポンス 200:
  ```json
  {
    "access_token": "<JWT>",
    "token_type": "bearer",
    "expires_in": 86400
  }
  ```
  ※ `expires_in` は `JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60` 秒。
- エラー:
  - 401: `{"detail":"Incorrect email or password"}` または `{"detail":"Inactive user"}`
  - 422: バリデーションエラー

#### POST `/api/auth/refresh`
- 概要: 有効なユーザートークンを再発行します。
- 認証: 必須
- リクエストボディ: なし
- レスポンス 200: `login` と同じ形式。
- エラー:
  - 401: トークン無効／期限切れ

#### GET `/api/auth/me`
- 概要: 現在のユーザー情報を取得します。
- 認証: 必須
- レスポンス 200:
  ```json
  {
    "id": "<uuid>",
    "email": "user@example.com",
    "username": "user-name",
    "is_active": true,
    "created_at": "2025-09-01T12:34:56+00:00"
  }
  ```
- エラー:
  - 401: トークン無効／期限切れ

#### PUT `/api/auth/me`
- 概要: ユーザー名やパスワードを更新します。
- 認証: 必須
- リクエストボディ（任意フィールドのみ送信）:
  ```json
  {
    "username": "new-name",
    "current_password": "old-pass",
    "new_password": "new-pass"
  }
  ```
  - `username`: 別ユーザーと重複不可。
  - パスワード変更時は `current_password` 必須。
- レスポンス 200: GET `/api/auth/me` と同じ。
- エラー:
  - 400: `Username already exists` / `Current password is required` / `Incorrect current password`
  - 401: トークン無効／期限切れ
  - 422: バリデーションエラー

#### DELETE `/api/auth/logout`
- 概要: サーバ側では状態を持たないログアウト。クライアントでトークンを破棄してください。
- 認証: 必須
- レスポンス 200: `{"message":"Successfully logged out"}`
- エラー: 401

### 4.2 会話管理 API
#### POST `/api/conversations`
- 概要: 新しい会話セッションを作成します。
- 認証: 必須
- リクエストボディ: なし
- レスポンス 200:
  ```json
  {
    "conversation_id": "<uuid>",
    "created_at": "2025-09-26T10:00:00+00:00",
    "updated_at": "2025-09-26T10:00:00+00:00"
  }
  ```
- エラー: 401

#### GET `/api/conversations`
- 概要: 会話リストを更新日時降順で取得します。
- 認証: 必須
- クエリパラメータ:
  - `skip` (int, デフォルト 0)
  - `limit` (int, デフォルト 20)
- レスポンス 200:
  ```json
  {
    "conversations": [
      {
        "id": "<uuid>",
        "title": "最初のユーザーメッセージ…",
        "created_at": "2025-09-26T10:00:00+00:00",
        "updated_at": "2025-09-26T10:05:00+00:00",
        "message_count": 3
      }
    ]
  }
  ```
- エラー: 401

#### GET `/api/conversations/{conversation_id}`
- 概要: 単一会話のメタ情報と全メッセージ履歴を取得します。
- 認証: 必須
- パスパラメータ:
  - `conversation_id` (UUID 文字列)
- レスポンス 200:
  ```json
  {
    "conversation": {
      "id": "<uuid>",
      "title": "最初のユーザーメッセージ…",
      "created_at": "2025-09-26T10:00:00+00:00",
      "updated_at": "2025-09-26T10:05:00+00:00"
    },
    "messages": [
      {
        "id": "<uuid>",
        "role": "user",
        "content": "こんにちは",
        "timestamp": "2025-09-26T10:00:00+00:00"
      }
    ]
  }
  ```
- エラー:
  - 401: 認証失敗
  - 404: 指定会話が存在しない、または別ユーザー所有

#### DELETE `/api/conversations/{conversation_id}`
- 概要: 会話と関連メッセージを削除します。
- 認証: 必須
- レスポンス 200: `{"message":"deleted"}`
- エラー:
  - 401
  - 404: 指定会話が存在しない、または別ユーザー所有

### 4.3 チャットSSE API
#### POST `/api/chat/stream/{conversation_id}`
- 概要: 指定会話にユーザーメッセージを追加し、AI応答を Server-Sent Events で逐次取得します。存在しない会話IDを指定した場合は同IDで新規作成されます（別ユーザーが所有するIDを指定した場合は404）。
- 認証: 必須
- ヘッダー: `Accept: text/event-stream`
- パスパラメータ: `conversation_id` (UUID 文字列。ただし新規作成時は任意文字列でも可。)
- リクエストボディ:
  ```json
  {
    "message": "こんにちは！",
    "conversation_id": "<uuid>"  // 省略可。省略時はパスのIDを使用。
  }
  ```
- ストリーム挙動:
  - イベントは `data: {"role": "assistant"|"tool", ...}` 形式のJSON文字列として送信。
  - アシスタント出力はトークン単位で `role: "assistant"`, `id: <assistant_message_id>` として送信され、`content` に差分テキストが格納される。
  - ツール実行完了時には `role: "tool"`, `content` に `{"tool_call_id", "tool_name", "output", "status"}` を含むJSON文字列が送信される。
  - ストリーム完了時には `event: done` とともに `data: {"id": <assistant_message_id>}` が送出される。
  - エラー発生時には `data: {"error": "エラーが発生しました: ..."}` が送信され、ストリームが終了する。
- 利用可能ツール（`tools.py` 定義）:
  - `get_current_time()`: 現在のUTC時刻を返却
  - `calculate(expression: str)`: 安全な数式を評価
  - `web_search(query: str, max_results: int = 5)`: モックの検索結果を返却
- 永続化フロー:
  1. ユーザーメッセージがDBに保存される。
  2. ストリーム終了後、アシスタント応答とツールメッセージがDBに追加される。
  3. 会話の `title` が未設定かつ最初のユーザーメッセージが存在する場合、冒頭 50 文字から自動生成。
- エラー:
  - 401: 認証失敗
  - 404: 会話が別ユーザーに属している
  - 422: リクエストバリデーションエラー

## 5. 設定項目と依存関係
| 項目 | 環境変数 | デフォルト | 用途 |
| --- | --- | --- | --- |
| OpenAI APIキー | `OPENAI_API_KEY` | なし（必須） | Agents SDKで利用。|
| OpenAIモデル | `OPENAI_MODEL` | `gpt-4o` | チャットモデル指定。|
| 最大トークン数 | `OPENAI_MAX_TOKENS` | 1024 | 生成トークン上限。|
| 温度 | `OPENAI_TEMPERATURE` | 0.7 | 生成多様性。|
| DB接続 | `DB_PROTOCOL`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | なし（必須） | SQLAlchemy接続情報。|
| JWTシークレット | `JWT_SECRET_KEY` | なし（必須） | トークン署名鍵。|
| JWT有効期限 | `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 1440 | トークン有効期限（分）。|
| CORS関連 | `CORS_ORIGINS`, `CORS_ALLOW_METHODS`, `CORS_ALLOW_CREDENTIALS` | 各種デフォルトあり | クライアントとのクロスドメイン通信許可。|

## 6. 今後の拡張候補
- 400系エラー時にエラーコード/種別を付与し、クライアントでのハンドリングを容易化する。
- SSEイベントに `event:` フィールドを活用し、アシスタント/ツール/完了などを明示化する。
- OpenAPIドキュメントの自動生成を有効化し、RESTクライアントとの連携を効率化する。

