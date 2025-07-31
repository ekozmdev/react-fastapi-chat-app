# React FastAPI Chat Application

OpenAI GPT-4を使用したチャットアプリケーション。React + Viteフロントエンド、FastAPI + uvバックエンド、PostgreSQLデータベースで構成されています。

## 技術スタック

- **フロントエンド**: React + TypeScript + Vite 7 + React Router + Biome
- **バックエンド**: FastAPI 0.116+ + uv + Python 3.13 + Ruff
- **データベース**: PostgreSQL 16 + SQLAlchemy 2.0 + Alembic
- **認証**: JWT + bcrypt/Argon2
- **LLM**: OpenAI GPT-4o-mini (via openai-agents-python SDK)
- **リアルタイム通信**: Server-Sent Events (SSE)（認証付き）
- **ツール実行追跡**: リアルタイムツール実行状態表示（Phase 2実装）
- **コンテナ**: Docker + Docker Compose
- **Node.js**: 22+（Vite v7要件）

## プロジェクト構成

```
react-fastapi-chat-app/
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── AuthContext.tsx
│   │   ├── LoginForm.tsx
│   │   ├── MarkdownRenderer.tsx
│   │   ├── ProtectedRoute.tsx
│   │   ├── main.tsx
│   │   └── index.css
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
│   │   │   ├── tool_execution.py
│   │   │   └── user.py
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── common.py
│   │   │   └── conversation.py
│   │   ├── clients.py
│   │   ├── main.py
│   │   ├── tools.py
│   │   └── tool_execution_manager.py
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
- **真のリアルタイムツール実行表示**: LLM決定瞬間での即座スピナー表示（人工遅延なし）
- **Claudeライクなデザイン**: モダンでクリーンなUI
- **会話履歴**: PostgreSQLデータベースでチャット履歴を永続化（ユーザー別）
- **会話管理**: 複数の会話を作成・切り替え・削除
- **ルーティング**: React Routerによる適切なURL管理
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

**DATABASE_URLについて**

本プロジェクトではPostgreSQLドライバーとしてpsycopg3を使用しているため、DATABASE_URLのプロトコルは `postgresql+psycopg://` を指定します。

```bash
# 正しい形式（psycopg3使用）
DATABASE_URL=postgresql+psycopg://chatuser:chatpassword@localhost:5432/chatdb

# 古い形式（psycopg2）は使用しない
# DATABASE_URL=postgresql://chatuser:chatpassword@localhost:5432/chatdb
```

psycopg3の利点：
- 非同期処理のネイティブサポート
- 優れたパフォーマンス
- モダンなPython 3.8+対応

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

### ルーティング

- `/` - メインチャット画面（認証必須）
- `/login` - ログインページ
- `/chat/:conversationId` - 特定の会話表示
- 404 - 存在しないパスは `/` にリダイレクト

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
- `POST /api/chat/stream/{conversation_id}` - リアルタイムチャットストリーミング

### REST エンドポイント
- `POST /api/conversations` - 新規会話の作成
- `GET /api/conversations` - 会話一覧の取得
- `GET /api/conversations/{conversation_id}` - 特定の会話の詳細
- `DELETE /api/conversations/{conversation_id}` - 会話の削除

### 認証エンドポイント
- `POST /api/auth/login` - ユーザーログイン
- `POST /api/auth/refresh` - トークンリフレッシュ
- `GET /api/auth/me` - 現在のユーザー情報取得
- `PUT /api/auth/me` - ユーザー情報更新
- `DELETE /api/auth/logout` - ログアウト

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
- `role`: ロール (user/assistant/system)
- `content`: メッセージ内容
- `tool_metadata`: ツールメタデータ (JSON) - Phase 1互換
- `has_detailed_executions`: 詳細実行データ有無 (Boolean)
- `created_at`: 作成日時

### tool_executions テーブル（Phase 2）
- `id`: 実行ID (UUID)
- `message_id`: メッセージID (外部キー)
- `tool_name`: ツール名
- `tool_arguments`: ツール引数 (JSON)
- `call_status`: 呼び出し状態
- `execution_status`: 実行状態
- `tool_output`: ツール出力
- `execution_time_ms`: 実行時間 (ミリ秒)
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

### デザインのカスタマイズ

`frontend/src/App.css`でスタイルを調整できます。

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
```

## トラブルシューティング

### データベース接続エラー
- PostgreSQLが起動しているか確認
- `.env`ファイルのDATABASE_URLが正しいか確認
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

### uv関連のエラー
```bash
# uvの再インストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# キャッシュクリア
uv cache clean

# 依存関係の再インストール
uv sync --no-cache
```

## ライセンス

MIT License

## 更新履歴

- 2025年7月: Phase 1-4完了・レイヤー型アーキテクチャ採用
  - **Phase 1-2**: ツール実行追跡とリアルタイム表示実装
  - **Phase 3-4**: 真のリアルタイムツール検出（ResponseOutputItemAddedEvent）
  - **レイヤー型アーキテクチャ**: core/, db/, schemas/, models/分離
  - **外部APIクライアント管理**: clients.pyでDependency Injection実装
  - **コード品質向上**: Biome/Ruff統一、TypeScript安全性向上

- 2025年7月: openai-agents-python SDK導入
  - 直接のOpenAI API呼び出しからopenai-agents-python SDKに移行
  - モデル: GPT-4o-mini採用（高速・低コスト）
  - システムプロンプトをAgent.instructionsで管理
  - エージェント機能拡張の基盤構築
  - 既存のSSEストリーミング機能完全維持

- 2025年7月: SSE版リリース
  - WebSocketからServer-Sent Events (SSE)への移行完了
  - HTTPベースの認証（Authorizationヘッダー）
  - Function Calling/MCP対応の基盤実装
  - UIアニメーション最適化

- 2025年7月: 開発環境最新化
  - Vite v7.0.5対応・Node.js 22+要件対応
  - Poetry → uv移行完了
  - PostgreSQL 16 + SQLAlchemy 2.0
  - FastAPI 0.116+対応