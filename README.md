# React FastAPI Chat Application

OpenAI GPT-4を使用したチャットアプリケーション。

React + Viteフロントエンド、FastAPI + uvバックエンド、PostgreSQLデータベースで構成されています。

## 技術スタック

- **フロントエンド**: React + TypeScript + Vite 7 + React Router v7 + Biome
- **バックエンド**: FastAPI 0.116+ + uv + Python 3.13 + Ruff
- **データベース**: PostgreSQL 16 + SQLAlchemy 2.0 + Alembic
- **認証**: JWT + bcrypt/Argon2
- **LLM**: OpenAI GPT-4o-mini (via openai-agents-python SDK)
- **リアルタイム通信**: Server-Sent Events (SSE)（認証付き）
- **アーキテクチャ**: レイヤー型アーキテクチャ（2025年ベストプラクティス）
- **コンテナ**: Docker + Docker Compose
- **Node.js**: 22+（Vite v7要件）

## プロジェクト構成

```
react-fastapi-chat-app/
├── frontend/
│   ├── src/
│   │   ├── auth/
│   │   │   ├── AuthContext.tsx
│   │   │   ├── LoginRoute.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   ├── pages/
│   │   │   ├── Chat.tsx
│   │   │   ├── Login.tsx
│   │   │   └── NotFound.tsx
│   │   ├── styles/
│   │   │   ├── App.css
│   │   │   └── index.css
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── types.ts
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── biome.json
│   ├── package.json
│   └── Dockerfile
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── deps.py
│   │   │   └── security.py
│   │   ├── db/
│   │   │   └── session.py
│   │   ├── models/
│   │   │   ├── base.py
│   │   │   ├── conversation.py
│   │   │   └── user.py
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   └── common.py
│   │   ├── clients.py
│   │   ├── main.py
│   │   ├── tools.py
│   ├── alembic/
│   │   └── versions/
│   ├── scripts/
│   │   └── manage_users.py
│   ├── pyproject.toml
│   ├── alembic.ini
│   └── Dockerfile
├── nginx/
│   └── nginx.conf
├── .env
├── .env.example
├── CLAUDE.md
└── compose.yaml
```

## 機能

- **JWT認証システム**: セキュアなユーザー認証とセッション管理
- **リアルタイムチャット**: Server-Sent Events (SSE)を使用したストリーミング応答（認証付き）
- **効率的なツール実行処理**: OpenAI Agents SDKのRunItemStreamEventによる安定したツール処理
- **高度なストリーミング処理**: ResponseTextDeltaEventとResponseFunctionCallArgumentsDeltaEventの分離によるクリーンな会話体験
- **リアルタイムツール検出**: ResponseOutputItemAddedEventによる即座のツール決定検出
- **Claudeライクなデザイン**: モダンでクリーンなUI
- **会話履歴**: PostgreSQLデータベースでチャット履歴を永続化（ユーザー別）
- **会話管理**: 複数の会話を作成・切り替え・削除
- **モダンルーティング**: React Router v7のOutletパターンによる保護ルート実装
- **404エラーハンドリング**: ユーザーフレンドリーな専用エラーページ（`/not-found-error`）
- **画面更新対応**: 会話URL直アクセス時の履歴復元（useEffect最適化）
- **レスポンシブデザイン**: モバイル対応
- **高速な開発環境**: Viteによる高速HMR

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd react-fastapi-chat-app
```

### 2. 環境変数の設定

```bash
# .env.exampleをコピーして.envを作成（プロジェクトルート）
cp .env.example .env

# .envファイルを編集してOPENAI_API_KEYを設定
# OPENAI_API_KEY=sk-...
```

**データベース設定について**

本プロジェクトでは個別コンポーネント設定を使用してDATABASE_URLを動的構築します。

```bash
# 個別コンポーネント設定（推奨）
DB_PROTOCOL=postgresql+psycopg
DB_HOST=localhost
DB_PORT=5432
DB_USER=chatuser
DB_PASSWORD=chatpassword
DB_NAME=chatdb
```

設定の利点：
- 環境別設定の柔軟性
- セキュリティ（パスワード分離）
- Docker環境との互換性
- psycopg3ドライバーによる高性能

### 3. Dockerを使用した起動

```bash
# Docker Composeで全サービスを起動（DB、バックエンド、フロントエンド）
docker compose up -d

# ログを確認
docker compose logs -f
```

アプリケーションは http://localhost でアクセスできます。

### 4. 開発環境での起動（Docker不使用）

#### PostgreSQLのセットアップ
```bash
# PostgreSQLをインストールして起動
# macOS: brew install postgresql && brew services start postgresql
# Ubuntu: sudo apt-get install postgresql && sudo systemctl start postgresql

# データベースとユーザーを作成
createdb chatdb
createuser chatuser -P
# パスワード: chatpassword
```

#### バックエンド (uv)
```bash
cd backend

# uvのインストール（未インストールの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 依存関係のインストール
uv sync

# データベースマイグレーション  
uv run alembic upgrade head

# 初期ユーザーの作成
uv run scripts/manage_users.py register

# 開発サーバー起動
uv run uvicorn app.main:app --reload --port 8000 --reload-dir app --log-level debug
```

#### フロントエンド (Vite)
```bash
cd frontend

# 依存関係のインストール
npm install

# 開発サーバー起動
npm run dev

# コードフォーマット・リント
npm run lint    # Biome lint with fix and error-on-warnings
npm run format  # Biome format
npm run check   # Biome check
```

## 開発サーバーの起動

### 開発環境での起動手順

1. **PostgreSQLを起動**
2. **バックエンドサーバーを起動**（ターミナル1）
   ```bash
   cd backend
   uv run uvicorn app.main:app --reload --port 8000
   ```
3. **フロントエンドサーバーを起動**（ターミナル2）
   ```bash
   cd frontend  
   npm run dev
   ```

### アクセス方法

- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://localhost:8000
- **API文書**: http://localhost:8000/docs (Swagger UI)

### 認証システム

アプリケーションは認証必須です：

1. **ユーザー作成**: 管理スクリプトでユーザーを作成
   ```bash
   cd backend
   uv run python scripts/manage_users.py register
   ```

2. **ログイン**: フロントエンドでメールアドレスとパスワードを入力

3. **動作確認用アカウント**:
   - 初回セットアップ時に管理スクリプトで作成
   - デフォルトでは作成されないため、手動で作成が必要

### 開発時の注意点

- **プロキシ設定**: Viteが `/api/*` をバックエンドにプロキシ
- **CORS**: 開発環境では `*` を許可（本番では要変更）
- **SSE認証**: AuthorizationヘッダーでJWTトークンを送信
- **自動ログイン**: JWTトークンがlocalStorageに保存される

### ルーティング（React Router v7 Outlet パターン）

- `/` - メインチャット画面（認証必須）
- `/login` - ログインページ（認証済みの場合は自動リダイレクト）
- `/chat/:conversationId?` - 特定の会話表示（認証必須）
- `/not-found-error` - 404エラーページ（会話履歴が見つからない場合）
- `*` - 未定義パスはルートへリダイレクト

**アーキテクチャ特徴**:
- **BrowserRouter**: `main.tsx`で設定（2025年ベストプラクティス）
- **ProtectedRoute**: Outletパターンで子ルートを保護
- **LoginRoute**: 認証状態に基づく動的ルーティング

## 本番環境へのデプロイ

### 1. Reactアプリのビルド

```bash
cd frontend
npm run build
```

### 2. バックエンドのビルド

```bash
cd backend
uv build
```

### 3. Dockerイメージのビルド

```bash
docker compose build
docker compose up -d
```

## API仕様

### Server-Sent Events (SSE) エンドポイント
- `POST /api/chat/stream` - リアルタイムチャットストリーミング（conversation_idはリクエストボディで指定）

### REST エンドポイント
- `GET /api/conversations` - 会話一覧の取得
- `GET /api/conversations/{conversation_id}` - 特定の会話の詳細
- `DELETE /api/conversations/{conversation_id}` - 会話の削除

### 認証エンドポイント
- `POST /api/auth/login` - ユーザーログイン
- `POST /api/auth/refresh` - トークンリフレッシュ
- `GET /api/auth/me` - 現在のユーザー情報取得

## データベーススキーマ

### conversations テーブル
- `id`: 会話ID (UUID)
- `user_id`: ユーザーID (外部キー)
- `title`: 会話タイトル
- `created_at`: 作成日時
- `updated_at`: 更新日時

### messages テーブル
- `id`: メッセージID (UUID)
- `conversation_id`: 会話ID (外部キー)
- `role`: ロール (user/assistant/tool)
- `content`: メッセージ内容（ツールの場合はJSON形式）
- `created_at`: 作成日時


### users テーブル
- `id`: ユーザーID (UUID)
- `email`: メールアドレス (ユニーク)
- `hashed_password`: ハッシュ化パスワード
- `is_active`: アクティブ状態
- `created_at`: 作成日時

## カスタマイズ

### LLMモデル・設定の変更

`backend/app/clients.py`の以下の部分を変更：
```python
# Chat Agent 初期化
self.chat_agent = Agent(
    name="ChatAssistant",
    instructions="""あなたは親切で知識豊富なアシスタントです。
    ユーザーの質問に正確かつ丁寧に答えてください。
    必要に応じてツールを使用してください。
    時刻の取得や計算が必要な場合は、適切なツールを使用してください。
    """,
    model=ModelSettings(model="gpt-4o-mini"),  # ここを変更
    tools=AVAILABLE_TOOLS,
)
```

利用可能なモデル（openai-agents-python SDK経由）:
- `gpt-4o-mini` (高速・低コスト・現在使用中)
- `gpt-4o` (高性能)
- `gpt-3.5-turbo` (旧モデル)
- `o1-preview` (推論特化)
- `o1-mini` (推論特化・軽量)

### ツール機能の追加・カスタマイズ

`backend/app/tools.py`で新しいツールを追加できます：

```python
@function_tool
def your_custom_tool(param1: str, param2: int) -> str:
    """カスタムツールの説明"""
    # ツールの処理ロジック
    return "結果"

AVAILABLE_TOOLS = [
    get_current_time,
    calculate, 
    web_search,
    your_custom_tool,  # 新しいツールを追加
]
```

現在利用可能なツール:
- **get_current_time**: 現在の時刻を取得
- **calculate**: 数式計算（安全な式のみ）
- **web_search**: Web検索（Mock版）

#### ツールのストリーミング処理

OpenAI Agents SDKによるツール処理の流れ：

1. **ツール呼び出し検出**: `RunItemStreamEvent`の`tool_called`イベントで即座に検出
2. **ツール実行**: バックエンドでツールを実行
3. **結果ストリーミング**: `tool_output`イベントで結果をリアルタイムにSSE送信
4. **データベース保存**: role:tool形式でメッセージとして保存

```json
{
  "role": "tool",
  "content": "{\"tool_call_id\": \"call_123\", \"tool_name\": \"get_current_time\", \"output\": \"2025-08-07 07:46:18 UTC\", \"status\": \"success\"}"
}
```

### デザインのカスタマイズ

`frontend/src/styles/App.css`でスタイルを調整できます。

#### CSS変数によるテーマカスタマイズ

本プロジェクトでは**CSS変数**を使用した統一されたカラーシステムを採用しており、簡単にテーマをカスタマイズできます：

```css
:root {
  /* 背景色 */
  --background-primary: #ffffff;
  --background-secondary: #f7f7f8;
  --background-tertiary: #f3f3f3;
  
  /* テキスト色 */
  --text-primary: #333;
  --text-secondary: #666;
  --text-muted: #999;
  
  /* アクセント色 */
  --accent-blue: #3b82f6;
  --accent-green: #10a37f;
  --accent-purple: #667eea;
}
```

**カスタマイズのメリット**:
- **一貫性**: 全コンポーネントで統一された色使用
- **保守性**: 色変更が一箇所で完結
- **テーマ変更**: ダークモード等の実装が容易

## 主要なアーキテクチャの特徴

### OpenAI Agent SDKストリーミング処理

本プロジェクトは**openai-agents-python SDK**を使用し、以下の高度なストリーミング処理を実装しています：

#### イベント処理システム

**低レベルイベント（RawResponsesStreamEvent）**
- **ResponseTextDeltaEvent**: AI応答のリアルタイム文字単位ストリーミング
- **ResponseFunctionCallArgumentsDeltaEvent**: ツール引数の受信（AI応答から完全分離）
- **ResponseOutputItemAddedEvent**: 新しい応答アイテム追加の瞬間検出

**高レベルイベント（RunItemStreamEvent）**
- **message_output_created**: 完成したメッセージの作成
- **tool_called**: ツール呼び出しの即座検出
- **tool_output**: ツール実行結果の受信

#### 通常メッセージのストリーミングフロー

```python
# 1. API呼び出し
result = Runner.run_streamed(chat_agent, api_messages)
async for event in result.stream_events():
    
    # 2. テキストデルタイベント処理
    if isinstance(event, RawResponsesStreamEvent):
        if isinstance(event.data, ResponseTextDeltaEvent):
            content = event.data.delta  # 文字単位でのリアルタイム受信
            assistant_content += content
            
            # 3. SSEでフロントエンドへ送信
            content_event = {
                "role": "assistant",
                "content": content,
                "id": assistant_id
            }
            yield f"data: {json.dumps(content_event)}\n\n"
```

#### ツール実行ストリーミングフロー

```python
# 1. ツール呼び出し検出
if hasattr(event, "item") and event.item.type == "tool_call_item":
    # ツール情報を即座に抽出・追跡
    tool_name = getattr(raw_item, "name", "unknown")
    call_id = getattr(event.item, "id", generate_unique_id())

# 2. ツール実行完了
elif event.item.type == "tool_call_output_item":
    # 結果を即座にSSE送信
    tool_event = {
        "role": "tool",
        "content": json.dumps({
            "tool_call_id": call_id,
            "tool_name": tool_name,
            "output": output,
            "status": "success"
        }),
        "id": call_id,
        "timestamp": datetime.now(UTC).isoformat()
    }
    yield f"data: {json.dumps(tool_event)}\n\n"
```

#### フロントエンドでのSSE受信処理

```javascript
// EventSource接続
const eventSource = new EventSource(url, { headers: { Authorization: `Bearer ${token}` }});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.role === 'assistant') {
    // リアルタイム文字追加
    setMessages(prev => updateLastMessage(prev, data.content));
  } else if (data.role === 'tool') {
    // ツール結果の表示
    const toolData = JSON.parse(data.content);
    displayToolExecution(toolData);
  }
};
```

#### レスポンス変形処理の特徴

**AI応答とツール引数の完全分離**
- `ResponseFunctionCallArgumentsDeltaEvent`を意図的に無視
- AI応答のストリーミングをクリーンに保持
- ツール引数はバックグラウンドで処理

**コード構造最適化**
- **active_tools最小限マッピング**: 複雑な`tool_tracking`辞書を大幅簡素化（70行→30行）
- **高レベルイベント活用**: RunItemStreamEventによるコード品質向上（57%改善）
- **技術的負債完全解消**: 不要コメント削除、統一リファクタリング
- **SDK公式イベントモデル準拠**: 堅牢で安定した処理を実現

## ユーザー管理

アプリケーションのユーザー管理は専用スクリプトで行います：

```bash
cd backend

# ユーザー一覧表示
uv run python scripts/manage_users.py list

# 新規ユーザー登録（対話形式）
uv run python scripts/manage_users.py register

# ユーザー有効化
uv run python scripts/manage_users.py activate user@example.com

# ユーザー無効化
uv run python scripts/manage_users.py deactivate user@example.com

# ユーザー削除
uv run python scripts/manage_users.py delete user@example.com
```

## uv コマンド

```bash
# 依存関係の追加
uv add <package>

# 開発依存関係の追加  
uv add --group dev <package>

# 依存関係のインストール
uv sync

# スクリプトの実行
uv run <script>

# フォーマット
uv run ruff format app/

# リント
uv run ruff check app/

# テスト実行
uv run pytest

# Requirements ファイルエクスポート
uv export --format requirements-txt --output-file requirements.txt          # 本番用
uv export --format requirements-txt --dev --output-file requirements_dev.txt  # 開発用
```

## トラブルシューティング

### データベース接続エラー
- PostgreSQLが起動しているか確認
- `.env`ファイルのデータベース設定（DB_PROTOCOL, DB_HOST等）が正しいか確認
- Docker使用時は`docker compose ps`でpostgresサービスが起動しているか確認

### SSE接続エラー
- CORSの設定を確認
- Viteのプロキシ設定を確認
- Nginxのプロキシ設定を確認
- Authorizationヘッダーが正しく送信されているか確認

### OpenAI APIエラー
- `.env`ファイルのAPIキーが正しいか確認
- APIキーの利用制限を確認
- 使用しているモデルが利用可能か確認
- 新しいResponses APIへの移行を検討（より高機能）

### ツール実行エラー
- ツールの定義を確認（`backend/app/tools.py`）
- ツールの引数が正しいか確認
- OpenAI SDKのイベントハンドリングを確認

### uv関連のエラー
```bash
# uvの再インストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# キャッシュクリア
uv cache clean

# 依存関係の再インストール
uv sync --no-cache
```

## 更新履歴

**最新バージョン** (2025年8月)
- **Phase 3完了**: SDK イベント処理の根本的リファクタリング、RunItemStreamEvent活用による安定性向上
- **フロントエンドアーキテクチャ現代化**: React Router v7 Outlet パターン、pages/構造、BrowserRouter最適配置
- **データ構造シンプル化**: role:toolメッセージ形式採用、tool_execution削除、SSEストリーミング安定化
- **レイヤー型アーキテクチャ**: core/, db/, schemas/, models/分離、外部APIクライアント管理
- **開発環境最新化**: openai-agents-python SDK導入、Vite v7.0.5対応、uv移行完了

詳細な変更履歴は各Phaseドキュメント（phase1.md, phase3.md等）を参照してください。