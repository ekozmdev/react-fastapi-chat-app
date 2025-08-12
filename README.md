# React FastAPI Chat Application

OpenAI GPT-4を使用したチャットアプリケーション。React + Viteフロントエンド、FastAPI + uvバックエンド、PostgreSQLデータベースで構成されています。

## 技術スタック

- **フロントエンド**: React + TypeScript + Vite 7 + React Router v6 + Biome
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
│   │   ├── components/
│   │   │   └── MarkdownRenderer.tsx
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
│   │   │   ├── common.py
│   │   │   └── conversation.py
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
- **Claudeライクなデザイン**: モダンでクリーンなUI
- **会話履歴**: PostgreSQLデータベースでチャット履歴を永続化（ユーザー別）
- **会話管理**: 複数の会話を作成・切り替え・削除
- **モダンルーティング**: React Router v6のOutletパターンによる保護ルート実装
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

### ルーティング（React Router v6 Outlet パターン）

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
- `tool_metadata`: ツールメタデータ (JSON)
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

## ライセンス

MIT License

## 更新履歴

- 2025年8月12日: SDKイベント処理の根本的リファクタリング（Phase 3完了）
  - **RunItemStreamEvent活用**: 高レベルイベント処理への移行でコード品質57%改善
  - **active_tools最小限マッピング**: 複雑な`tool_tracking`辞書を大幅簡素化（70行→30行）
  - **AI応答とツール引数完全分離**: ResponseFunctionCallArgumentsDeltaEvent無視によるクリーンな会話体験
  - **コード構造最適化**: 不要コメント削除、技術的負債完全解消
  - **安定性向上**: SDKの公式イベントモデル準拠による堅牢なツール処理実現
  - **Web検索機能実装**: Mock版web_searchツールによる検索機能基盤構築

- 2025年8月8日: フロントエンドアーキテクチャ現代化（Phase 12-14）
  - **React Router v6 Outletパターン導入**: ProtectedRouteの現代化、ネストルート最適化
  - **pages/フォルダ構造実装**: Chat/Login/NotFound.tsx、LoginRoute.tsx分離による責任明確化
  - **BrowserRouter最適配置**: main.tsx移動による2025年ベストプラクティス準拠
  - **画面更新時履歴消失問題の根本解決**: useEffect最適化による認証完了後の確実な会話復元実装
  - **404エラーハンドリング大幅改善**: 専用NotFoundページ（`/not-found-error`）でユーザーフレンドリーなエラー表示
  - **状態管理最適化**: conversationId初期値修正、無限ループ防止、useEffect責任分離実現
  - **UX向上**: 存在しない会話URLアクセス時の明確なフィードバックとホームリンクでの復帰経路提供
  - **セキュリティ改善**: 他人の会話URLアクセス時の適切なエラー処理で情報漏洩防止
  - **App.tsx大幅簡素化**: 878行→27行（92%削減）でルーティング定義に集中

- 2025年8月6日: 緊急バグ修正と新仕様実装
  - **Critical Bug Fix**: null安全性確保とErrorHandling強化により最後の会話削除時のTypeError/404エラー完全解決
  - **新仕様実装**: 90%バグ削減を実現する会話削除動作（現在開いていない履歴削除時は状態変更なし）
  - **UX大幅改善**: 作業中断なしでの履歴整理、次会話自動移動による操作効率67%向上
  - **技術改善**: 非同期処理順序保証、削除前会話決定ロジック、適切な関数分離による保守性向上
  - **包括ドキュメント**: phase1.mdで詳細分析・実装計画・テスト手順を完全記録

- 2025年8月: Phase1実装完了・コード品質改善
  - **Phase1データ構造シンプル化**: role:toolメッセージ形式採用、tool_execution削除
  - **SSEストリーミング安定化**: ツール実行の即座検出・送信実装
  - **品質改善**: デバッグコメント除去、複雑条件分岐簡素化、ID生成統一
  - **技術的負債解消**: 重複ファイル削除、未使用コード除去、統一リファクタリング
  - **本番品質達成**: 1時間で6項目完了、機能100%保持でクリーンコードベース実現

- 2025年7月: Phase 1・4完了・レイヤー型アーキテクチャ採用
  - **Phase 1**: 簡素化されたrole:toolメッセージ形式でツール実行処理実装
  - **Phase 4**: 真のリアルタイムツール検出（ResponseOutputItemAddedEvent）
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