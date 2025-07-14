# LLM Chat Application

OpenAI GPT-4を使用したチャットアプリケーション。React + Viteフロントエンド、FastAPI + uvバックエンド、PostgreSQLデータベースで構成されています。

## 技術スタック

- **フロントエンド**: React 18 + TypeScript + Vite 5 + React Router
- **バックエンド**: FastAPI 0.116+ + uv + Python 3.13
- **データベース**: PostgreSQL 16 + Alembic
- **認証**: JWT + bcrypt
- **LLM**: OpenAI GPT-4.1
- **リアルタイム通信**: Server-Sent Events (SSE)（認証付き）
- **コンテナ**: Docker + Docker Compose
- **Node.js**: 20.19+ または 22.12+（Vite要件）

## プロジェクト構成

```
llm-chat-app/
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   ├── main.tsx
│   │   └── index.css
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── Dockerfile
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py
│   ├── alembic/
│   │   └── env.py
│   ├── pyproject.toml
│   ├── poetry.lock
│   ├── alembic.ini
│   ├── .env
│   └── Dockerfile
├── nginx/
│   └── nginx.conf
└── docker-compose.yml
```

## 機能

- **JWT認証システム**: セキュアなユーザー認証とセッション管理
- **リアルタイムチャット**: Server-Sent Events (SSE)を使用したストリーミング応答（認証付き）
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
cd llm-chat-app
```

### 2. 環境変数の設定

```bash
# backend/.env.exampleをコピーして.envを作成
cp backend/.env.example backend/.env

# .envファイルを編集してOPENAI_API_KEYを設定
# OPENAI_API_KEY=sk-...
```

### 3. Dockerを使用した起動

```bash
# Docker Composeで全サービスを起動（DB、バックエンド、フロントエンド）
docker-compose up -d

# ログを確認
docker-compose logs -f
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
   uv run scripts/manage_users.py register
   ```

2. **ログイン**: フロントエンドでメールアドレスとパスワードを入力

3. **動作確認用アカウント**:
   - メール: `admin@invalid.com`
   - パスワード: `abcd1234`

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
poetry build
```

### 3. Dockerイメージのビルド

```bash
docker-compose build
docker-compose up -d
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
- `title`: 会話タイトル
- `created_at`: 作成日時
- `updated_at`: 更新日時

### messages テーブル
- `id`: メッセージID (UUID)
- `conversation_id`: 会話ID (外部キー)
- `role`: ロール (user/assistant/system)
- `content`: メッセージ内容
- `created_at`: 作成日時

## カスタマイズ

### LLMモデルの変更

`backend/app/main.py`の以下の部分を変更：
```python
response = client.chat.completions.create(
    model="gpt-4.1",  # ここを変更
    messages=api_messages,
    max_tokens=1024,
    temperature=0.7
)
```

利用可能なモデル（2025年6月時点）:
- `gpt-4.1` (最新・推奨)
- `gpt-4.1-mini` (高速・低コスト)
- `gpt-4.1-nano` (最速・最低コスト)
- `gpt-4o` (旧モデル)
- `gpt-3.5-turbo` (旧モデル)

### デザインのカスタマイズ

`frontend/src/App.css`でスタイルを調整できます。

## ユーザー管理

アプリケーションのユーザー管理は専用スクリプトで行います：

```bash
cd backend

# ユーザー一覧表示
uv run scripts/manage_users.py list

# 新規ユーザー登録（対話形式）
uv run scripts/manage_users.py register

# ユーザー有効化
uv run scripts/manage_users.py activate user@example.com

# ユーザー無効化
uv run scripts/manage_users.py deactivate user@example.com

# ユーザー削除
uv run scripts/manage_users.py delete user@example.com
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
- Docker使用時は`docker-compose ps`でpostgresサービスが起動しているか確認

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

### Poetry関連のエラー
```bash
# Poetry v2の再インストール
curl -sSL https://install.python-poetry.org | python3 - --uninstall
curl -sSL https://install.python-poetry.org | python3 -

# キャッシュクリア
poetry cache clear pypi --all

# 依存関係の再インストール
poetry install --no-cache
```

## ライセンス

MIT License

## 更新履歴

- 2025年7月: SSE版リリース
  - WebSocketからServer-Sent Events (SSE)への移行
  - HTTPベースの認証（Authorizationヘッダー）
  - Function Calling/MCP対応の基盤実装
  - UIアニメーション最適化

- 2025年6月: 最新バージョンに対応
  - React + Vite 5
  - Poetry → uv移行
  - OpenAI GPT-4.1モデル
  - FastAPI 0.111+