# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a React + FastAPI chat application with real-time Server-Sent Events (SSE) communication and OpenAI GPT integration. The project uses a monorepo structure with clear frontend/backend separation:

- **Frontend**: React + TypeScript (Node.js 22+)
- **Backend**: FastAPI (Python 3.13+) 
- **Database**: PostgreSQL 16
- **Infrastructure**: Docker Compose with Nginx reverse proxy
- **LLM**: OpenAI GPT integration via openai-agents-python SDK

## Development Commands

### Frontend (in `/frontend/`)
```bash
npm run dev          # Start Vite dev server on :3000
npm run build        # Build for production (runs tsc + vite build)  
npm run lint         # Biome lint with fix and error-on-warnings
npm run format       # Biome format
npm run check        # Biome check
npm run preview      # Preview production build
```

### Backend (in `/backend/`)
```bash
uv run uvicorn app.main:app --reload --port 8000  # Start FastAPI dev server
uv run alembic upgrade head                        # Run database migrations
uv run ruff check                                  # Lint Python code
uv run ruff format                                 # Format Python code
uv run pytest                                      # Run tests
```

**Note**: When testing or debugging backend changes, the user should start the server manually using the uvicorn command above. Claude should not attempt to start the server during development/testing sessions.

### Docker Environment
```bash
docker-compose up -d    # Start all services (PostgreSQL, FastAPI, Nginx)
docker-compose logs -f  # View logs
docker-compose ps       # Check service status
```

## Project Structure

```
/frontend/              # React TypeScript app
  /src/                 # React source code
  vite.config.ts        # Vite configuration with proxy to backend
  
/backend/               # FastAPI application
  /app/                 # Application code
    /core/              # Core infrastructure layer
      config.py         # Application settings and configuration
      deps.py           # Dependency injection utilities
      security.py       # JWT authentication and password handling
    /db/                # Database layer
      session.py        # Database connection and session management
    /models/            # SQLAlchemy database models
      __init__.py       # Model imports for app-wide access
      base.py           # SQLAlchemy Base declaration
      user.py           # User model
      conversation.py   # Conversation and Message models
      tool_execution.py # Tool execution tracking model
    /schemas/           # Pydantic data validation schemas
      auth.py           # Authentication request/response schemas
      common.py         # Common shared schemas
      conversation.py   # Conversation-related schemas
    clients.py          # External API client management (OpenAI, Agents)
    main.py             # FastAPI app with routes and business logic
    tools.py            # Tool definitions for agent interactions
    tool_execution_manager.py # Tool execution lifecycle management
  /alembic/             # Database migrations
  /scripts/             # Management scripts (user management, etc.)
  pyproject.toml        # uv dependencies and ruff configuration
  
/nginx/                 # Nginx reverse proxy configuration
compose.yaml            # Docker Compose orchestration
```

## Key Architecture Patterns

### Communication
- **Development**: Vite dev server proxies `/api/*` to FastAPI backend
- **Production**: Nginx serves React app and proxies API to FastAPI
- **Real-time**: Server-Sent Events (SSE) streaming for chat responses at `/api/chat/stream/{conversation_id}`
- **REST API**: CRUD operations for conversations and messages
- **Authentication**: JWT tokens via Authorization header for secure SSE connections

### Database Schema
- `conversations`: id (UUID), title, created_at, updated_at
- `messages`: id (UUID), conversation_id (FK), role, content, created_at, tool_metadata (JSON), has_detailed_executions (Boolean)
- `tool_executions`: id (UUID), message_id (FK), tool_name, tool_arguments (JSON), call_status, execution_status, tool_output, execution_time_ms, etc. (Phase 2)
- Uses UUID primary keys and proper foreign key relationships

### Technology Migration Notes
- **Dependency Management**: Migrated from Poetry to uv (COMPLETED)
- **Real-time Communication**: Migrated from WebSocket to Server-Sent Events (SSE) (COMPLETED)
- **LLM Integration**: Migrated from direct OpenAI API calls to openai-agents-python SDK (COMPLETED)
- **Architecture**: Implemented layered architecture with core/, db/, schemas/ separation (COMPLETED)
- **External API Management**: Implemented clients.py with Dependency Injection + Lifespan Events (COMPLETED)
- **Tool Execution**: Phase 2 detailed tool execution tracking with database persistence (COMPLETED)
- **Real-time Tool Detection**: Phase 4 instant tool decision detection via ResponseOutputItemAddedEvent (COMPLETED)
- Uses openai-agents SDK with Agent/ModelSettings pattern for LLM interactions
- SSE provides foundation for Function Calling/MCP tool status display
- Agent-based architecture enables multi-agent and tool integration features
- All code written in Japanese documentation style (see existing files)

### Tool Use Implementation (Phase 1, 2, 3, 4)
- **Phase 1**: Basic tool functionality with minimal frontend changes
  - Tools defined in `app/tools.py` with `@function_tool` decorator
  - `AVAILABLE_TOOLS` list for easy extension
  - `tool_metadata` JSON column in messages table for backward compatibility
- **Phase 2**: Real-time tool execution visualization (COMPLETED)
  - `ToolExecution` table for detailed execution tracking
  - `ToolExecutionManager` class for database-connected tool lifecycle management
  - Real-time SSE events: `tool_start`, `tool_complete` with execution details
  - Frontend UI components for tool execution status display with spinners and success/error states
  - Uses `RunItemStreamEvent` from openai-agents SDK for proper tool lifecycle tracking
  - Both Phase 1 (tool_metadata) and Phase 2 (detailed executions) data are preserved
- **Phase 3**: JSON引数混入問題の根本的解決 (COMPLETED)
  - `ResponseTextDeltaEvent` vs `ResponseFunctionCallArgumentsDeltaEvent` 型分離実装
  - AI応答とツール引数の完全分離によりクリーンな会話体験実現
  - ポストプロセシングフィルタリング排除、SDK正式利用パターン採用
- **Phase 4**: 真のリアルタイムツール検出実装 (COMPLETED)
  - **Phase 4.1**: deepwiki公式確認による技術的実現可能性確定
  - **Phase 4.2**: `ResponseOutputItemAddedEvent`による革新的実装
    - LLM決定瞬間での即座スピナー表示（人工遅延完全排除）
    - 双方向重複防止ロジックで順序不問対応
    - 空文字列エラーハンドリング、全エッジケース対応
    - `tool_decision` SSEイベント型追加で既存互換性100%維持

## Environment Setup

### Required Environment Variables (in `/.env`)
- `OPENAI_API_KEY`: OpenAI API key for GPT integration
- `DATABASE_URL`: PostgreSQL connection string

### Environment Variable Best Practices (Phase 0 Lessons)

#### Docker Compose Environment Variables
Docker Composeで環境変数を使用する際は、**2段階の設定**が必要です：

1. **Docker Compose変数置換**: プロジェクトルートの`.env`ファイルから変数を読み込み
2. **コンテナ環境変数**: `environment`セクションで明示的にコンテナに変数を渡す

```yaml
# compose.yaml
services:
  fastapi:
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}  # .envから置換
      DATABASE_URL: ${DATABASE_URL}      # .envから置換
```

#### Python環境変数読み込みベストプラクティス
```python
# 推奨パターン
from dotenv import find_dotenv, load_dotenv

dotenv_path = find_dotenv()
print(f"[CONFIG] Loading .env from: {dotenv_path}")  # デバッグ用
load_dotenv(dotenv_path)
```

**メリット**:
- プロジェクトルートの.envを確実に検出
- 実行場所に依存しない堅牢性
- ログ出力による可視性向上

### Development Dependencies
- Node.js 22+ 
- Python 3.13+
- PostgreSQL 16

## Code Conventions

### Python (Backend)
- Uses ruff for linting and formatting (line length: 88)
- Target Python version: 3.13+
- SQLAlchemy 2.0 async patterns
- FastAPI dependency injection for database sessions
- Pydantic models for validation
- Layered architecture: core/, schemas/, db/, models/ separation

### TypeScript (Frontend)
- Strict TypeScript configuration
- Biome for linting and formatting with `--fix --error-on-warnings` options
- Minimal external dependencies (only React essentials)
- Component-based architecture

## Testing

- Backend: pytest with asyncio support
- Run tests with: `uv run pytest`

## Pre-Commit Checklist

コミット前に必ず以下の確認手順を実施してください：

### 1. コード品質チェック

#### フロントエンド（`/frontend/`）
```bash
npm run lint         # Biome lint with fix and error-on-warnings
npm run format       # Biome format (必要に応じて)
npm run check        # Biome check
```

#### バックエンド（`/backend/`）
```bash
uv run ruff check    # Ruff lint check
uv run ruff format   # Ruff format (必要に応じて)
uv run pytest       # テスト実行（可能な場合）
```

### 2. ステージング内容のセルフレビュー

```bash
git status           # 変更ファイル一覧確認
git diff --staged    # ステージング内容の詳細確認
```

**レビューポイント：**
- 意図しない変更が含まれていないか
- コミットメッセージに含める変更内容の把握
- 機密情報（APIキー、パスワード等）が含まれていないか
- デバッグ用コード・コメントが残っていないか

### 3. コミット実行

品質チェックとセルフレビューが完了後、コミットを実行：

```bash
git commit -m "適切なコミットメッセージ"
```

**Note**: この手順により、コードベースの品質維持とレビュー効率の向上を実現できます。

## Development Lessons Learned (Phase 0-9実装エッセンス)

### Environment & Configuration Management
- **Phase 0**: 環境変数管理の最適化 - .envファイルのプロジェクトルート移動、find_dotenv()による堅牢な自動検出、Docker Compose環境変数の2段階設定パターン、ログ出力による可視化とデバッグ性向上

### Architecture & Database Design Patterns
- **Phase 1**: アーキテクチャ分離手法 - models/ディレクトリによるSQLAlchemyモデル分離、alembic依存関係管理の重要性
- **Phase 2**: 段階的ツール導入 - @function_toolデコレータによる拡張可能設計、tool_metadata軽量データ保存アプローチ
- **Phase 3**: 詳細実行追跡 - ToolExecutionManagerクラスによる2段階ステータス管理、マイグレーション・データベース設計のベストプラクティス

### SDK Integration & Event Handling
- **Phase 4**: openai-agents-python SDK正式活用 - ResponseTextDeltaEvent vs ResponseFunctionCallArgumentsDeltaEventの型分離、フィルタリング削除による根本的アーキテクチャ改善
- **Phase 5**: 真のリアルタイム実装 - ResponseOutputItemAddedEventによる即座スピナー表示、双方向重複防止ロジック、deepwiki技術レビュー手法

### UI/UX Design Patterns
- **Phase 6**: ChatGPT風サイドバー設計 - `<`/`>`アイコンによる直感的トグルUI、CSS transition活用のスムーズアニメーション
- **Phase 7**: Flexboxレイアウト最適化 - margin-top: autoによる下部固定配置テクニック、最小限CSS変更での効果的UI改善
- **Phase 8**: データ永続化修復 - バックエンドAPIとフロントエンド期待値の不整合解決、convert_tool_metadata_to_executions変換パターン
- **Phase 9**: コンパクトボタン設計 - CSS中央配置ベストプラクティス（margin: autoの活用）、段階的UI簡素化手法

### Code Quality & Best Practices
- **Phase 10**: 統合コード品質改善 - 
  - フロントエンド: SVGアクセシビリティ対応（WCAG 2.1 AA準拠）、キーボードナビゲーション実装、TypeScript安全性向上（non-null assertion削除）
  - バックエンド: 現代的型アノテーション（Dict→dict、List→list、Optional→T|None）、セキュリティ改善（eval→ast.literal_eval）、未使用インポート削除
  - 自動化: Biome/Ruffによる統一コードフォーマット、適切なlint警告サプレス手法

### Architecture Refactoring & Code Optimization
- **Phase 11**: 軽いリファクタリング・大規模クリーンアップ - 
  - **段階的リファクタリング**: 機能破壊ゼロでレイヤー型アーキテクチャ導入（core/設定・認証・依存性、schemas/型定義、db/データ層分離）
  - **安全なクリーンアップ**: 重複コード・デッドコード・未使用ファイルの体系的特定と削除（1171行・30%削減達成）
  - **品質保証プロセス**: インポートテスト・機能動作確認による段階的検証、SSE/ツール機能100%保持
  - **保守性向上戦略**: uv依存関係管理一元化、実験的コード識別・分離、明確な責任分離による構造改善

### Development Process Insights
- **段階的実装の重要性**: 複雑機能を小さなPhaseに分割することで確実な進捗管理
- **技術制約の早期把握**: 外部ライブラリ（openai-agents SDK）の制約を理解した設計変更
- **ユーザビリティ重視**: 複雑な設計から実用的なシンプル設計への方向転換
- **データ互換性確保**: Phase間でのデータ移行・変換パターンの確立
- **外部APIクライアント管理**: Dependency Injection + Lifespan Eventsによるリソース効率化、main.pyからの責任分離によるアーキテクチャ改善（clients.py分離パターン）
- **リファクタリング時の注意点**: インポート削除時の依存関係追跡の重要性、使用箇所の完全な特定によるコード整合性確保