# Phase 1: 環境変数化推奨設定リスト

## 概要

バックエンドコードベースを詳細に分析した結果、環境変数化すべきハードコード値を特定しました。
セキュリティ向上、運用性改善、設定の柔軟性向上を目的として、以下の値を環境変数化することを推奨します。

## 現在の状況

### ✅ 既に環境変数化済み

| 環境変数名 | ファイル | 説明 |
|-----------|---------|------|
| `OPENAI_API_KEY` | `app/core/config.py:19` | OpenAI API キー |
| `DATABASE_URL` | `app/core/config.py:22` | データベース接続URL |

## 🔥 最優先（セキュリティリスク）

### 1. JWT認証設定

**ファイル**: `app/core/security.py`

| 現在の値 | 推奨環境変数名 | 理由 |
|---------|--------------|------|
| `JWT_SECRET_KEY = "your-secret-key-here"` | `JWT_SECRET_KEY` | **セキュリティリスク高**: デフォルト値のまま本番運用すると認証が無効化 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 1440` | `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | トークン有効期限の環境別設定 |

**注意**: `JWT_ALGORITHM`はセキュリティ上固定値推奨（環境変数化は設定ミスリスクが高い）

### 2. CORS設定（セキュリティリスク）

**ファイル**: `app/core/config.py:25-28`

| 現在の値 | 推奨環境変数名 | 理由 |
|---------|--------------|------|
| `CORS_ORIGINS = ["*"]` | `CORS_ORIGINS` | **セキュリティリスク**: 全オリジン許可は本番環境で危険 ※カンマ区切りで設定 |
| `CORS_ALLOW_CREDENTIALS = True` | `CORS_ALLOW_CREDENTIALS` | 認証情報送信可否の制御 ※ブール値変換必要 |
| `CORS_ALLOW_METHODS = ["*"]` | `CORS_ALLOW_METHODS` | 許可HTTPメソッドの制限 ※カンマ区切りで設定 |

**注意**: `CORS_ALLOW_HEADERS`は通常`["*"]`のままで問題なし（環境変数化不要）

## 🟡 高優先（運用性向上）

### 3. アプリケーション基本設定

**ファイル**: `app/core/config.py:15-16`

| 現在の値 | 推奨環境変数名 | 理由 |
|---------|--------------|------|
| `APP_TITLE = "LLM Chat API"` | `APP_TITLE` | 環境別API名の設定 |

### 4. サーバー設定

**ファイル**: `app/main.py:576`

| 現在の値 | 推奨環境変数名 | 理由 |
|---------|--------------|------|
| `host="0.0.0.0"` | `FASTAPI_HOST` | ホストバインドアドレスの設定 |
| `port=8000` | `FASTAPI_PORT` | ポート番号の環境別設定 |

### 5. OpenAI/Agent設定

**ファイル**: `app/clients.py:33-36`

| 現在の値 | 推奨環境変数名 | 理由 |
|---------|--------------|------|
| `model="gpt-4o"` | `OPENAI_MODEL` | モデル選択の柔軟性 |
| `max_tokens=1024` | `OPENAI_MAX_TOKENS` | トークン数制限の調整 |
| `temperature=0.7` | `OPENAI_TEMPERATURE` | 応答の創造性レベル調整 |

## 🟢 中優先（設定統一・保守性向上）

### 6. データベースフォールバック設定

**ファイル**: `app/db/session.py:12`

```python
# 現在のフォールバック値
"postgresql+psycopg://chatuser:chatpassword@localhost:5432/chatdb"
```

| 推奨環境変数名 | 理由 |
|--------------|------|
| ~~`DATABASE_URL_FALLBACK`~~ | ~~デフォルトDB接続先の明示的設定~~ **→ constants.pyパターンで実装済み** |

## 🟢 低優先（特殊用途・デバッグ）

### 7. アプリケーションバージョン

**ファイル**: `app/core/config.py:16`

| 現在の値 | 推奨環境変数名 | 理由 |
|---------|--------------|------|
| `APP_VERSION = "0.2.0"` | `APP_VERSION` | CI/CDでの自動バージョン設定（通常はビルド時決定） |

### 8. デバッグ用ツール設定

**ファイル**: `app/tools.py:17`

| 現在の値 | 推奨環境変数名 | 理由 |
|---------|--------------|------|
| `time.sleep(5)` | `TOOL_EXECUTION_DELAY` | デバッグ用遅延時間の調整（本番では不要） |

## 📦 Docker/インフラ設定

### 9. Docker Compose設定

**ファイル**: `compose.yaml`

| 現在の値 | 推奨環境変数名 | 理由 |
|---------|--------------|------|
| `POSTGRES_USER: chatuser` | `POSTGRES_USER` | DB認証情報の分離 |
| `POSTGRES_PASSWORD: chatpassword` | `POSTGRES_PASSWORD` | DB認証情報の分離 |
| `POSTGRES_DB: chatdb` | `POSTGRES_DB` | DB名の環境別設定 |
| ポート設定（5432, 8000, 80） | `POSTGRES_PORT`, `FASTAPI_PORT`, `NGINX_PORT` | ポート競合回避 |

### 10. Alembic設定

**ファイル**: `alembic.ini:57`

| 現在の値 | 推奨環境変数名 | 理由 |
|---------|--------------|------|
| `sqlalchemy.url = postgresql+psycopg://...` | `ALEMBIC_DATABASE_URL` | マイグレーション用DB接続の分離 |

## 実装優先度

### Phase 1: 緊急対応（セキュリティリスク）
1. `JWT_SECRET_KEY` - 強力なシークレットキーの設定（現在デフォルト値で危険）
2. `CORS_ORIGINS` - 本番環境での適切なオリジン制限（現在全オリジン許可）
3. `CORS_ALLOW_CREDENTIALS` - 認証情報送信の適切な制御

### Phase 2: 運用改善
1. `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` - トークン有効期限の環境別設定
2. `CORS_ALLOW_METHODS` - 許可HTTPメソッドの制限
3. OpenAI設定の柔軟化（`OPENAI_MODEL`, `OPENAI_MAX_TOKENS`, `OPENAI_TEMPERATURE`）
4. サーバー設定の環境変数化（`FASTAPI_HOST`, `FASTAPI_PORT`）
5. アプリケーション基本設定（`APP_TITLE`）
6. セキュリティポリシー設定（`MIN_PASSWORD_LENGTH`）

### Phase 3: インフラ統一
1. Docker環境の完全な環境変数化（`DOCKER_EXPOSE_PORT`等）
2. Nginx設定の環境変数化（`NGINX_PORT`, `NGINX_LISTEN_PORT`, `NGINX_FASTAPI_PORT`, `NGINX_PROXY_TIMEOUT`）
3. Alembic設定の分離（`ALEMBIC_DATABASE_URL`）
4. ~~データベースフォールバック設定の明示化（`DATABASE_URL_FALLBACK`）~~ **→ constants.pyパターンで実装済み**
5. PostgreSQL設定の統一（`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_PORT`）

## 推奨.envファイル例

```bash
# JWT認証設定（最重要）
JWT_SECRET_KEY=your-super-secure-secret-key-here-change-this-immediately
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS設定（本番環境では制限必須）
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE

# アプリケーション設定
APP_TITLE=LLM Chat API
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

# OpenAI設定
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=1024
OPENAI_TEMPERATURE=0.7

# データベース設定
DATABASE_URL=postgresql+psycopg://user:password@host:port/dbname
# DATABASE_URL_FALLBACK は不要（constants.pyのDEFAULT_DATABASE_URLで管理）

# PostgreSQL（Docker）
POSTGRES_USER=chatuser
POSTGRES_PASSWORD=chatpassword
POSTGRES_DB=chatdb
POSTGRES_PORT=5432

# Nginx設定
NGINX_PORT=80
NGINX_LISTEN_PORT=80
NGINX_FASTAPI_PORT=8000
NGINX_PROXY_TIMEOUT=86400

# Docker設定
DOCKER_EXPOSE_PORT=8000

# セキュリティポリシー
MIN_PASSWORD_LENGTH=8

# Alembic
ALEMBIC_DATABASE_URL=postgresql+psycopg://user:password@host:port/dbname
```

## 実装時の注意点

### 1. JWT設定の環境変数化実装例

```python
# app/core/security.py での実装例
import os

# JWT設定（環境変数化）
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY or JWT_SECRET_KEY == "your-secret-key-here":
    raise ValueError("JWT_SECRET_KEY must be set to a secure value")

JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
)
```

### 2. CORS設定のパース処理

環境変数でカンマ区切り文字列を受け取る場合、コード側で配列に変換する処理が必要です：

```python
# app/core/config.py での実装例
def parse_cors_origins(origins_str: str) -> list[str]:
    """CORS オリジンのパース処理"""
    if not origins_str or origins_str == "*":
        return ["*"]
    return [origin.strip() for origin in origins_str.split(",")]

def parse_bool(value: str) -> bool:
    """文字列からブール値への変換"""
    return value.lower() in ("true", "1", "yes", "on")

class Settings:
    # CORS設定（環境変数化）
    CORS_ORIGINS: list[str] = parse_cors_origins(os.getenv("CORS_ORIGINS", "*"))
    CORS_ALLOW_CREDENTIALS: bool = parse_bool(os.getenv("CORS_ALLOW_CREDENTIALS", "true"))
    CORS_ALLOW_METHODS: list[str] = (
        os.getenv("CORS_ALLOW_METHODS", "*").split(",") 
        if os.getenv("CORS_ALLOW_METHODS") != "*" 
        else ["*"]
    )
```

### 3. OpenAI設定の環境変数化実装例

```python
# app/clients.py での実装例
from .core.config import settings

class APIClients:
    async def initialize(self):
        # OpenAI クライアント初期化
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        # Chat Agent 初期化（環境変数対応）
        self.chat_agent = Agent(
            name="ChatAssistant",
            instructions="""...""",
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            model_settings=ModelSettings(
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "1024")),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            ),
            tools=AVAILABLE_TOOLS,
        )
```

### 4. エラーハンドリングとバリデーション

```python
# app/core/config.py での実装例
import os
from typing import Any

def validate_required_env(key: str) -> str:
    """必須環境変数の検証"""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Required environment variable '{key}' is not set")
    return value

def safe_int(value: str, default: int) -> int:
    """安全な整数変換"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value: str, default: float) -> float:
    """安全な浮動小数点変換"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

class Settings:
    # 必須設定（検証付き）
    OPENAI_API_KEY: str = validate_required_env("OPENAI_API_KEY")
    JWT_SECRET_KEY: str = validate_required_env("JWT_SECRET_KEY")
    
    # オプション設定（デフォルト値付き）
    OPENAI_MAX_TOKENS: int = safe_int(os.getenv("OPENAI_MAX_TOKENS"), 1024)
    OPENAI_TEMPERATURE: float = safe_float(os.getenv("OPENAI_TEMPERATURE"), 0.7)
```

## まとめ

### セルフレビュー実施済み

このドキュメントは技術的正確性、優先度分類、実装可能性の観点から詳細レビューを実施しています。

**包括的ファイル調査実施**: 全バックエンドファイル（`app/`, `alembic/`, `scripts/`, `Dockerfile`, `nginx.conf`, `compose.yaml`）を再調査し、当初見落としていた以下の環境変数化対象を発見・追加しました：

- **Docker関連**: `DOCKER_EXPOSE_PORT`
- **Nginx関連**: `NGINX_PORT`, `NGINX_LISTEN_PORT`, `NGINX_FASTAPI_PORT`, `NGINX_PROXY_TIMEOUT`
- **セキュリティポリシー**: `MIN_PASSWORD_LENGTH`

### 現状分析

- ✅ **実装済み**: 基本的な環境変数化（`OPENAI_API_KEY`、`DATABASE_URL`）
- 🔥 **緊急対応必要**: `JWT_SECRET_KEY`のデフォルト値（`"your-secret-key-here"`）
- 🔥 **セキュリティリスク**: CORS全オリジン許可（`["*"]`）設定

### 推奨されない設定

以下の項目は検討したが、セキュリティまたは実用性の観点から推奨しません：
- `JWT_ALGORITHM` - セキュリティ上固定値推奨
- `CORS_ALLOW_HEADERS` - 通常`["*"]`で問題なし

### 実装アプローチ

段階的実装（Phase 1→2→3）により、セキュリティリスクの早期解決と運用性改善を両立できます。
特に**JWT_SECRET_KEY**の即座対応が必要です。

## 実装推奨環境変数一覧

| 優先度 | 環境変数名 | 設定例 | 意味・理由 |
|-------|-----------|-------|----------|
| 🔥 | `JWT_SECRET_KEY` | `your-super-secure-random-key-256bit` | **最重要**: JWTトークン署名用秘密鍵。現在デフォルト値で認証無効化リスク |
| 🔥 | `CORS_ORIGINS` | `http://localhost:3000,https://example.com` | CORS許可オリジン。現在`["*"]`で全オリジン許可（本番環境で危険） |
| 🔥 | `CORS_ALLOW_CREDENTIALS` | `true` | 認証情報（Cookie、Authorization header）送信許可制御 |
| 🟡 | `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | JWTトークン有効期限（分）。環境別でセキュリティレベル調整 |
| 🟡 | `CORS_ALLOW_METHODS` | `GET,POST,PUT,DELETE` | CORS許可HTTPメソッド。現在`["*"]`で全メソッド許可 |
| 🟡 | `OPENAI_MODEL` | `gpt-4o` | 使用するOpenAIモデル。コスト・性能バランス調整 |
| 🟡 | `OPENAI_MAX_TOKENS` | `1024` | AI応答の最大トークン数。応答長制御・コスト管理 |
| 🟡 | `OPENAI_TEMPERATURE` | `0.7` | AI応答の創造性レベル（0.0-2.0）。用途に応じた調整 |
| 🟡 | `FASTAPI_HOST` | `0.0.0.0` | FastAPIサーバーのバインドホスト。セキュリティ・アクセス制御 |
| 🟡 | `FASTAPI_PORT` | `8000` | FastAPIサーバーのポート番号。環境別ポート競合回避 |
| 🟡 | `APP_TITLE` | `LLM Chat API` | API仕様書に表示されるアプリケーション名 |
| ✅ | ~~`DATABASE_URL_FALLBACK`~~ | ~~`postgresql+psycopg://chatuser:chatpass@localhost:5432/chatdb`~~ | **constants.pyパターンで実装済み** |
| 🟢 | `POSTGRES_USER` | `chatuser` | PostgreSQLユーザー名（Docker環境） |
| 🟢 | `POSTGRES_PASSWORD` | `secure-db-password` | PostgreSQLパスワード（Docker環境） |
| 🟢 | `POSTGRES_DB` | `chatdb` | PostgreSQLデータベース名（Docker環境） |
| 🟢 | `POSTGRES_PORT` | `5432` | PostgreSQLポート番号。ポート競合回避 |
| 🟢 | `ALEMBIC_DATABASE_URL` | `postgresql+psycopg://user:pass@host:5432/db` | Alembicマイグレーション用DB接続URL |
| 🟢 | `NGINX_PORT` | `80` | Nginx外部公開ポート（compose.yaml）。ポート競合回避 |
| 🟢 | `NGINX_LISTEN_PORT` | `80` | Nginx内部リッスンポート（nginx.conf）。サーバー設定 |
| 🟢 | `NGINX_FASTAPI_PORT` | `8000` | NginxからFastAPIへのプロキシポート（nginx.conf） |
| 🟢 | `NGINX_PROXY_TIMEOUT` | `86400` | Nginxプロキシタイムアウト秒数（nginx.conf）。長期接続制御 |
| 🟢 | `DOCKER_EXPOSE_PORT` | `8000` | DockerコンテナEXPOSEポート（Dockerfile）。コンテナネットワーク設定 |
| 🟡 | `MIN_PASSWORD_LENGTH` | `8` | パスワード最小文字数（scripts/manage_users.py）。セキュリティポリシー |
| 🔧 | `APP_VERSION` | `0.2.0` | アプリケーションバージョン。CI/CD自動設定用 |
| 🔧 | `TOOL_EXECUTION_DELAY` | `2` | ツール実行デバッグ用遅延秒数。本番環境では不要 |

**優先度凡例:**
- 🔥 **緊急対応**: セキュリティリスク（即座対応必要）- 3項目
- 🟡 **高優先**: 運用改善（推奨実装）- 9項目
- 🟢 **中優先**: インフラ統一（環境整備）- 11項目
- 🔧 **低優先**: 特殊用途・デバッグ - 2項目

**合計: 25項目の環境変数化推奨**

## 最小限実装セット

本番環境での最低限必要な環境変数：

```bash
# 必須（セキュリティ）
JWT_SECRET_KEY=your-super-secure-random-key-256bit
CORS_ORIGINS=https://yourdomain.com

# 必須（既存）
OPENAI_API_KEY=your-openai-api-key
DATABASE_URL=postgresql+psycopg://user:password@host:5432/dbname
```

**注意**: `JWT_SECRET_KEY`は最低32文字以上のランダム文字列を使用してください。

## 環境変数実装時の変更ファイル一覧

.envファイルに環境変数を移行する場合、以下のファイルを変更する必要があります：

### 📝 **設定読み込み系ファイル（修正必要）**

| ファイル | 変更内容 | 優先度 |
|---------|----------|-------|
| `backend/app/core/security.py` | **dotenv追加必要**: `load_dotenv()`を追加してos.getenv()を.env対応 | 🔥 緊急 |
| `backend/alembic/env.py` | **dotenv追加必要**: `load_dotenv()`を追加してDATABASE_URL読み込み対応 | 🟡 高優先 |
| `backend/app/core/config.py` | **拡張必要**: 新しい環境変数のos.getenv()を追加 | 🟡 高優先 |
| `backend/app/clients.py` | **修正必要**: ハードコードされた`"gpt-4o"`, `1024`, `0.7`を環境変数化 | 🟡 高優先 |
| `backend/app/main.py` | **修正必要**: ハードコードされた`host="0.0.0.0"`, `port=8000`を環境変数化 | 🟡 高優先 |
| `backend/app/tools.py` | **修正必要**: `time.sleep(5)`を環境変数`TOOL_EXECUTION_DELAY`で制御 | 🔧 低優先 |
| `backend/scripts/manage_users.py` | **修正必要**: パスワード長制限`len(password) < 8`を環境変数化 | 🟡 高優先 |

### 🐳 **Docker/インフラ系ファイル（修正必要）**

| ファイル | 変更内容 | 優先度 |
|---------|----------|-------|
| `compose.yaml` | **env_file追加**: `env_file: - ./backend/.env`を各サービスに追加 | 🟢 中優先 |
| `compose.yaml` | **環境変数参照**: `POSTGRES_USER: ${POSTGRES_USER}`形式に変更 | 🟢 中優先 |
| `backend/Dockerfile` | **ARG/ENVに変更**: `EXPOSE ${DOCKER_EXPOSE_PORT:-8000}`に変更 | 🟢 中優先 |
| `backend/Dockerfile` | **CMD修正**: `--port ${FASTAPI_PORT:-8000}`を環境変数参照に変更 | 🟢 中優先 |
| `nginx/nginx.conf` | **envsubst対応**: テンプレート化して`${NGINX_LISTEN_PORT}`等を変数参照 | 🟢 中優先 |
| `backend/alembic.ini` | **環境変数参照**: `sqlalchemy.url`を`postgresql+psycopg://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}`に変更 | 🟢 中優先 |

### ✅ **既に.env対応済みファイル（変更不要）**

| ファイル | 対応状況 |
|---------|----------|
| `backend/app/core/config.py` | ✅ `load_dotenv()`済み、基本的な環境変数読み込み実装済み |
| `backend/init_db.py` | ✅ `load_dotenv()`済み、DATABASE_URL対応済み |
| `backend/scripts/manage_users.py` | ✅ `load_dotenv()`済み、DATABASE_URL対応済み |

### 🆕 **新規作成が必要なファイル**

| ファイル | 内容 | 優先度 |
|---------|------|-------|
| `backend/.env` | 全環境変数の設定ファイル（25項目） | 🔥 緊急 |
| `backend/.env.example` | .envのテンプレートファイル（セキュア値を除外） | 🟡 高優先 |
| `nginx/nginx.conf.template` | envsubst用Nginxテンプレートファイル | 🟢 中優先 |

### 🔧 **特殊な変更パターン**

#### 1. **nginx.conf の環境変数対応**
```bash
# 現在
listen 80;
server fastapi:8000;

# 変更後（template使用）
listen ${NGINX_LISTEN_PORT};
server fastapi:${NGINX_FASTAPI_PORT};
```

#### 2. **compose.yaml の env_file 対応**
```yaml
# 変更前
environment:
  POSTGRES_USER: chatuser
  POSTGRES_PASSWORD: chatpassword

# 変更後
env_file:
  - ./backend/.env
environment:
  POSTGRES_USER: ${POSTGRES_USER}
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

#### 3. **Dockerfile の ARG/ENV パターン**
```dockerfile
# 変更前
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# 変更後
ARG DOCKER_EXPOSE_PORT=8000
ARG FASTAPI_PORT=8000
EXPOSE ${DOCKER_EXPOSE_PORT}
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${FASTAPI_PORT}"]
```

### 📋 **実装チェックリスト**

#### Phase 1: 緊急セキュリティ対応
- [ ] `backend/.env`ファイル作成
- [ ] `backend/app/core/security.py`にdotenv追加
- [ ] JWT_SECRET_KEY強化

#### Phase 2: コアファイル修正
- [ ] `backend/app/core/config.py`拡張
- [ ] `backend/app/clients.py`のOpenAI設定環境変数化
- [ ] `backend/alembic/env.py`にdotenv追加

#### Phase 3: Docker/インフラ対応
- [ ] `compose.yaml`のenv_file対応
- [ ] `nginx/nginx.conf.template`作成とenvsubst対応
- [ ] `backend/Dockerfile`のARG/ENV対応

**重要**: この順序で実装することで、セキュリティリスクを最小化しながら段階的に環境変数化を進められます。

## 🚀 2025年最新ベストプラクティス調査結果

WebSearch・MCP・context7を使用して、リストアップした環境変数について2025年最新のベストプラクティスを調査しました。重要な発見と推奨事項をまとめます。

### 📋 **1. FastAPI環境変数管理の現代的アプローチ**

**重要な変更**: Pydantic v2では`BaseSettings`のインポート元が変更されました。

```python
# ❌ 旧方式（Pydantic v1）
from pydantic import BaseSettings

# ✅ 2025年推奨（Pydantic v2）
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8", 
        case_sensitive=False
    )
    
    # 詳細な型指定とバリデーション
    jwt_secret_key: str = Field(..., min_length=32, description="JWT signing secret")
    cors_origins: list[str] = Field(default=["*"], description="CORS allowed origins")
    openai_api_key: str = Field(..., description="OpenAI API key")

@lru_cache()  # パフォーマンス最適化（ファイル読み込み回数削減）
def get_settings():
    return Settings()
```

**推奨理由**: `@lru_cache()`により「ファイル読み込みは通常コストが高い（遅い）操作」を回避し、リクエスト毎の.env読み込みを防ぎます。

### 🔐 **2. JWT認証セキュリティ（2025年基準）**

**重大な発見**: 現在のコードは最新セキュリティ基準を満たしていません。

| 項目 | 現在の実装 | 2025年推奨 | セキュリティ影響 |
|------|-----------|-----------|----------------|
| **アルゴリズム** | `HS256` | **RS256** | HS256は共有秘密鍵、RS256は公開鍵暗号で安全 |
| **秘密鍵長** | デフォルト値 | **最低512bit** | 短い鍵はブルートフォース攻撃に脆弱 |
| **環境変数化** | 一部対応 | **完全分離** | デフォルト値での本番運用は認証無効化リスク |

**2025年推奨実装**:
```python
# security.py（2025年版）
import os
import secrets
from datetime import timedelta

# ✅ 推奨：RS256アルゴリズム（非対称暗号）
JWT_ALGORITHM = "RS256"  # 固定値（環境変数化は推奨されない）

# ✅ 強力な秘密鍵生成（開発時）
def generate_secure_key():
    return secrets.token_urlsafe(64)  # 512bit相当

# ✅ 厳格な環境変数検証
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY or JWT_SECRET_KEY == "your-secret-key-here":
    raise ValueError("JWT_SECRET_KEY must be set to a secure 512-bit value")

JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))  # デフォルト短縮
```

**Security Alert**: 「HS256のブルートフォース攻撃は確実に可能で、短く弱い秘密鍵使用時に発生」との2025年調査結果。

### 🐳 **3. Docker/Compose環境変数管理の新基準**

**重要**: 機密情報には環境変数ではなく**Docker Secrets**を使用することが2025年標準です。

**現在の問題**:
```yaml
# ❌ セキュリティリスク
environment:
  POSTGRES_PASSWORD: chatpassword  # 平文でパスワード露出
```

**2025年推奨方式**:
```yaml
# ✅ Docker Secrets使用
services:
  postgres:
    image: postgres:16-alpine
    secrets:
      - postgres_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
      POSTGRES_USER: ${POSTGRES_USER}  # 非機密はenv_file
    env_file:
      - ./backend/.env

secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt  # 開発環境
    # external: true  # 本番環境（外部秘密管理）
```

**理由**: 「環境変数は全プロセスで利用可能で、アクセス追跡が困難。デバッグ時にログ出力される恐れもある。Secretsはこれらのリスクを軽減」

### 🤖 **4. OpenAI API設定の最適化**

**2025年モデル選択指針**:
```python
# ✅ 2025年推奨設定
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")  # 最新・最高性能
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "1024"))  # コスト効率
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.0"))  # 事実確認用途は0推奨
```

**温度パラメータ指針**:
- **`temperature=0.0`**: データ抽出、事実確認Q&A（最も真実性が高い）
- **`temperature=0.9`**: 創造的アプリケーション
- **重要**: `temperature`と`top_p`は「同時使用禁止。片方を使う場合、もう片方は1に設定」

### 🌐 **5. CORS設定のセキュリティ強化**

**重大なセキュリティ問題**: 現在の`["*"]`設定は2025年基準では危険です。

```python
# ❌ 現在の危険な設定
CORS_ORIGINS = ["*"]
CORS_ALLOW_CREDENTIALS = True  # ←この組み合わせは許可されない

# ✅ 2025年セキュア設定
origins = [
    "https://yourdomain.com",
    "https://www.yourdomain.com", 
    # 開発時のみ: "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 明示的なドメイン指定
    allow_credentials=True,  # 認証情報使用時は origins=["*"] 禁止
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # 具体的メソッド指定
    allow_headers=["Content-Type", "Authorization"],  # 具体的ヘッダー指定
    max_age=3600,  # プリフライトキャッシュ
)
```

**セキュリティ原則**: 「`allow_origins`は認証情報許可時に`['*']`設定不可。オリジンは明示指定が必須」

### 📊 **推奨環境変数値の更新**

| 環境変数 | 従来推奨 | 2025年推奨 | 変更理由 |
|---------|---------|-----------|----------|
| `JWT_SECRET_KEY` | 任意の文字列 | 512bit以上のランダム値 | ブルートフォース攻撃対策 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` (24時間) | `15` (15分) | セキュリティ強化 |
| `CORS_ORIGINS` | `["*"]` | 具体的ドメイン列挙 | 認証情報使用時の必須要件 |
| `OPENAI_TEMPERATURE` | `0.7` | `0.0` | 事実確認用途での真実性向上 |
| `OPENAI_MODEL` | `gpt-4o-mini` | `gpt-4o` | 2025年最新・最高性能モデル |

### 🔥 **緊急対応が必要な項目**

1. **JWT_SECRET_KEY**: デフォルト値は即座に変更必須（認証迂回リスク）
2. **CORS設定**: `["*"]` + `credentials=True`は技術的に無効（エラー発生）
3. **Docker Secrets**: 本番環境でのパスワード平文化は重大なセキュリティリスク

### 📈 **実装優先度の再評価**

2025年基準では、以下の項目を最高優先に格上げします：
- `JWT_SECRET_KEY` → **🚨 Critical**
- `CORS_ORIGINS` → **🚨 Critical** 
- `CORS_ALLOW_CREDENTIALS` → **🚨 Critical**
- `OPENAI_API_KEY` → **🚨 Critical** （Docker Secrets移行）

### 🐘 **6. PostgreSQL Docker環境の新セキュリティ基準**

**重要**: 2025年では**PostgreSQL認証情報もDocker Secrets**が標準です。

**現在の危険な実装**:
```yaml
# ❌ セキュリティリスク
environment:
  POSTGRES_USER: chatuser
  POSTGRES_PASSWORD: chatpassword  # 平文パスワード露出
  POSTGRES_DB: chatdb
```

**2025年推奨実装**:
```yaml
# ✅ PostgreSQL用Docker Secrets
services:
  postgres:
    image: postgres:16.9  # 具体的バージョン指定
    environment:
      POSTGRES_USER_FILE: /run/secrets/postgres_user
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
      POSTGRES_DB_FILE: /run/secrets/postgres_db
    secrets:
      - postgres_user
      - postgres_password
      - postgres_db

secrets:
  postgres_user:
    file: ./secrets/postgres_user.txt
  postgres_password:
    file: ./secrets/postgres_password.txt  
  postgres_db:
    file: ./secrets/postgres_db.txt
```

**セキュリティ要点**:
- **_FILE環境変数**: PostgreSQL公式イメージは`POSTGRES_PASSWORD_FILE`等をサポート
- **具体的バージョン**: `postgres:latest`は避け、`postgres:16.9`等を明示指定
- **Secrets理由**: 「環境変数は全プロセスで利用可能で追跡困難。デバッグ時ログ出力リスクもある」

### 🌐 **7. Nginx環境変数テンプレート（2025年標準）**

**重要**: Nginx公式DockerイメージはコンテナーのためBUILT-IN環境変数テンプレートシステムを提供しています。

**現在の静的設定**:
```nginx
# ❌ ハードコード
server {
    listen 80;
    server fastapi:8000;
}
```

**2025年推奨テンプレート方式**:
```nginx
# ✅ /etc/nginx/templates/default.conf.template
server {
    listen ${NGINX_LISTEN_PORT};
    server_name _;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://fastapi:${NGINX_FASTAPI_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_read_timeout ${NGINX_PROXY_TIMEOUT};
    }
}
```

**Docker Compose設定**:
```yaml
# ✅ 2025年Nginx環境変数対応
services:
  nginx:
    image: nginx:alpine
    environment:
      NGINX_LISTEN_PORT: ${NGINX_LISTEN_PORT:-80}
      NGINX_FASTAPI_PORT: ${NGINX_FASTAPI_PORT:-8000}
      NGINX_PROXY_TIMEOUT: ${NGINX_PROXY_TIMEOUT:-86400}
    volumes:
      - ./nginx/templates:/etc/nginx/templates  # .templateファイル配置
    env_file:
      - ./backend/.env
```

**2025年テンプレート特徴**:
- **自動処理**: `.template`拡張子ファイルが自動的に`envsubst`処理される
- **変数保護**: Nginx内蔵変数（`$host`等）は誤変換されない
- **デフォルト値**: `${VAR:-default}`形式でデフォルト値設定可能

### 📊 **最終的な2025年環境変数設定推奨値**

調査結果を反映した更新推奨値:

| 環境変数 | 従来推奨 | **2025年最新推奨** | 変更根拠 |
|---------|---------|-------------------|----------|
| `JWT_ALGORITHM` | ❌`HS256` | **固定`RS256`** | 非対称暗号によるセキュリティ強化 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | **`15`** | セキュリティベストプラクティス |
| `POSTGRES_PASSWORD` | 環境変数 | **Docker Secrets** | 機密情報の適切な管理 |
| `OPENAI_TEMPERATURE` | `0.7` | **`0.0`** | 事実確認用途での真実性最大化 |
| `NGINX_PROXY_TIMEOUT` | `86400` | **動的設定** | 用途別最適化 |

### 🚨 **Critical Security Alerts（2025年基準）**

1. **JWT実装**: 現在のHS256は脆弱性あり → **RS256必須**
2. **CORS設定**: `["*"]` + credentials は**技術的に無効**
3. **PostgreSQL認証**: 平文パスワードは**重大セキュリティリスク**
4. **API鍵管理**: 環境変数使用は**2025年標準違反**

### 🔧 **緊急対応チェックリスト（優先度順）**

1. 🚨 **JWT_SECRET_KEY**: 512bit秘密鍵生成・設定
2. 🚨 **CORS_ORIGINS**: 具体的ドメイン列挙・`["*"]`除去  
3. 🚨 **PostgreSQL Secrets**: Docker Secrets移行
4. 🚨 **OpenAI API Key**: Docker Secrets移行
5. 🟡 **Nginx Template**: envsubst対応実装

**結論**: 現在の実装は2025年セキュリティ基準に照らすと**複数の重大な脆弱性**を含んでいます。特に**JWT認証、CORS設定、機密情報管理**の即座修正が必要です。Docker Secrets の採用により、真のゼロトラスト環境を実現できます。

---

## 🎯 Phase 1 実装TODOリスト

以下の25項目の環境変数化を優先度順に実装します。各項目は個別のタスクとして管理し、段階的な実装を行います。

### 🔥 最優先（セキュリティリスク） - 5項目

- [x] **JWT_SECRET_KEY**を環境変数化 (app/core/security.py)
  - ~~現在: デフォルト値 `"your-secret-key-here"`~~
  - ~~対応: 512bit以上の強力な秘密鍵設定~~
  - ~~リスク: 認証迂回の重大なセキュリティリスク~~
  - **実装済み**: `validate_required_env()`で必須環境変数化、未設定時はアプリ起動停止

- [x] **JWT_ACCESS_TOKEN_EXPIRE_MINUTES**を環境変数化 (app/core/security.py)
  - ~~現在: ハードコード `1440` (24時間)~~
  - ~~対応: 環境別トークン有効期限設定~~
  - ~~推奨: 本番環境では15分程度に短縮~~
  - **実装済み**: `constants.py`でデフォルト値管理、`config.py`でint型変換、`security.py`でsettings使用

- [x] ~~**CORS_ORIGINS**を環境変数化 (app/core/config.py)~~
  - ~~現在: 危険な設定 `["*"]`~~
  - ~~対応: 具体的ドメイン列挙~~
  - ~~リスク: 全オリジン許可は本番環境で危険~~
  - **実装済み**: `constants.py`でセキュアなデフォルト値、`config.py`でカンマ区切りリスト解析、`main.py`で適用

- [x] ~~**CORS_ALLOW_CREDENTIALS**を環境変数化 (app/core/config.py)~~
  - ~~現在: ハードコード `True`~~
  - ~~対応: 認証情報送信可否の制御~~
  - ~~注意: `origins=["*"]`との組み合わせは無効~~
  - **実装済み**: `constants.py`でデフォルト値、`config.py`でbool型解析、`main.py`で適用

- [x] ~~**CORS_ALLOW_METHODS**を環境変数化 (app/core/config.py)~~
  - ~~現在: 危険な設定 `["*"]`~~
  - ~~対応: 許可HTTPメソッドの明示的制限~~
  - ~~推奨: `["GET", "POST", "PUT", "DELETE"]`~~
  - **実装済み**: `constants.py`でセキュアなデフォルト値、`config.py`でカンマ区切りリスト解析、`main.py`で適用

### 🟡 高優先（運用性向上） - 9項目

- [ ] **APP_TITLE**を環境変数化 (app/core/config.py)
  - 現在: `"LLM Chat API"`
  - 対応: 環境別API名の設定

- [x] ~~**FASTAPI_HOST**を環境変数化 (app/main.py)~~
  - ~~現在: `"0.0.0.0"`~~
  - ~~対応: ホストバインドアドレスの設定~~
  - **対応不要**: 開発環境では固定値が適切、本番はuvicornコマンドで直接指定

- [x] ~~**FASTAPI_PORT**を環境変数化 (app/main.py)~~
  - ~~現在: `8000`~~
  - ~~対応: ポート番号の環境別設定~~
  - **対応不要**: プロジェクト内で8000ポート統一、Docker使用時はcompose.yamlで管理

- [x] **OPENAI_MODEL**を環境変数化 (app/clients.py)
  - 現在: `"gpt-4o"`
  - 対応: モデル選択の柔軟性

- [x] **OPENAI_MAX_TOKENS**を環境変数化 (app/clients.py)
  - ~~現在: `1024`~~
  - ~~対応: トークン数制限の調整~~
  - **実装済み**: `constants.py`でデフォルト値管理、`config.py`でint型変換、`clients.py`でsettings使用

- [x] **OPENAI_TEMPERATURE**を環境変数化 (app/clients.py)
  - ~~現在: `0.7`~~
  - ~~対応: 応答の創造性レベル調整~~
  - ~~推奨: 事実確認用途では `0.0`~~
  - **実装済み**: `constants.py`でデフォルト値管理、`config.py`でfloat型変換、`clients.py`でsettings使用

- [x] ~~**DATABASE_URL_FALLBACK**を環境変数化 (app/db/session.py)~~
  - ~~現在: ハードコードされたフォールバック値~~
  - ~~対応: デフォルトDB接続先の明示的設定~~
  - **実装済み**: `constants.py`の`DEFAULT_DATABASE_URL`で管理、`config.py`で`os.getenv()`パターン適用

- [ ] **POSTGRES_USER**を環境変数化 (compose.yaml)
  - 現在: `chatuser`
  - 対応: DB認証情報の分離

- [ ] **POSTGRES_PASSWORD**を環境変数化 (compose.yaml)
  - 現在: `chatpassword`
  - 対応: DB認証情報の分離
  - 推奨: Docker Secretsの使用

### 🟢 中優先（設定統一・保守性向上） - 9項目

- [ ] **POSTGRES_DB**を環境変数化 (compose.yaml)
  - 現在: `chatdb`
  - 対応: DB名の環境別設定

- [ ] **POSTGRES_PORT**を環境変数化 (compose.yaml)
  - 現在: `5432`
  - 対応: ポート競合回避

- [ ] **NGINX_PORT**を環境変数化 (compose.yaml)
  - 現在: `80`
  - 対応: ポート競合回避

- [ ] **NGINX_LISTEN_PORT**を環境変数化 (nginx.conf)
  - 現在: `80`
  - 対応: Nginx内部リッスンポート設定

- [ ] **NGINX_FASTAPI_PORT**を環境変数化 (nginx.conf)
  - 現在: `8000`
  - 対応: NginxからFastAPIへのプロキシポート

- [ ] **NGINX_PROXY_TIMEOUT**を環境変数化 (nginx.conf)
  - 現在: `86400`
  - 対応: プロキシタイムアウト制御

- [x] ~~**DOCKER_EXPOSE_PORT**を環境変数化 (Dockerfile)~~
  - ~~現在: `8000`~~
  - ~~対応: コンテナネットワーク設定~~
  - **対応不要**: プロジェクト内で8000ポート統一、compose.yamlでポートマッピング管理

- [ ] **ALEMBIC_DATABASE_URL**を環境変数化 (alembic.ini)
  - 現在: ハードコードされたDB URL
  - 対応: マイグレーション用DB接続の分離

- [x] ~~**MIN_PASSWORD_LENGTH**を環境変数化 (scripts/manage_users.py)~~
  - ~~現在: `8`~~
  - ~~対応: セキュリティポリシーの設定~~
  - **実装済み**: `constants.py`で`MIN_PASSWORD_LENGTH = 8`定数定義、`manage_users.py`でインポート使用

### 🔧 低優先（特殊用途・デバッグ） - 2項目

- [ ] **APP_VERSION**を環境変数化 (app/core/config.py)
  - 現在: `"0.2.0"`
  - 対応: CI/CDでの自動バージョン設定

- [ ] **TOOL_EXECUTION_DELAY**を環境変数化 (app/tools.py)
  - 現在: `time.sleep(5)`
  - 対応: デバッグ用遅延時間の調整

---

### 📊 実装進捗管理

**合計**: 25項目
- 🔥 **最優先**: 5項目（セキュリティリスク）
- 🟡 **高優先**: 9項目（運用性向上）
- 🟢 **中優先**: 9項目（設定統一）
- 🔧 **低優先**: 2項目（特殊用途）

### 🚀 次のステップ

1. **Phase 1.1**: 最優先5項目の緊急対応（セキュリティリスク解決）
2. **Phase 1.2**: 高優先9項目の実装（運用性向上）
3. **Phase 1.3**: 中優先9項目の実装（設定統一）
4. **Phase 1.4**: 低優先2項目の実装（完全性向上）

各段階完了後に動作確認とテストを実施し、品質を確保しながら段階的に進めます。

---

## 💡 実装中に得た教訓・学び

### 🔍 **環境変数デフォルト値処理での学び（OPENAI_MODEL実装時）**

#### **問題**: `or`演算子 vs `os.getenv(key, default)`の選択ミス

**発生した状況**:
DATABASE_URLの環境変数化実装時に、以下の2つのパターンで迷いが生じた：

```python
# パターン1: or演算子（一時的に採用してしまった）
DATABASE_URL: str = os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL

# パターン2: os.getenv標準パターン（正解）
DATABASE_URL: str = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
```

#### **原因分析**:

| 原因 | 詳細 | 影響度 |
|------|------|--------|
| **既存コードへの過度な配慮** | session.pyの`if settings.DATABASE_URL`パターンに影響を受けた | 🔴 高 |
| **一貫性への注意不足** | 既存のOPENAI_MODELパターンを見落とした | 🔴 高 |
| **設計判断の曖昧さ** | 空文字列を「未設定」として扱うべきか判断が曖昧だった | 🟡 中 |

#### **重要な学び**:

1. **一貫性を最優先にする**
   ```python
   # ✅ 既存パターンと統一（推奨）
   OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
   DATABASE_URL: str = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
   
   # ❌ 異なるパターンの混在（混乱の元）
   OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
   DATABASE_URL: str = os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL
   ```

2. **Pythonの標準パターンを尊重する**
   - `os.getenv(key, default)`はPython標準ライブラリの推奨パターン
   - 予期しない動作（空文字列の扱い等）を避けられる
   - チーム開発時の認知負荷が少ない

3. **既存コードに引っ張られすぎない**
   - 既存コードの設計が最適とは限らない
   - 新しい実装では一貫性のある設計を優先する
   - レガシーコードのパターンを無批判に踏襲しない

#### **設計指針**:
- **空文字列の扱い**: 通常は有効な値として扱い、デフォルト値は環境変数未設定時のみ使用
- **特殊要件**: 空文字列もデフォルト値にフォールバックさせたい場合は、明示的に設計判断として文書化する

この経験により、環境変数化の統一パターンとして**`os.getenv(key, default)`を標準採用**することが確定した。

### 📋 **環境変数化の標準実装パターン**

今回の実装で確立されたベストプラクティス：

#### **1. constants.pyでデフォルト値定義**
```python
# app/core/constants.py
"""アプリケーション定数定義"""

# OpenAI設定のデフォルト値
DEFAULT_OPENAI_MODEL = "gpt-4o"

# データベース設定のデフォルト値
DEFAULT_DATABASE_URL = "postgresql+psycopg://chatuser:chatpassword@localhost:5432/chatdb"
```

#### **2. config.pyで環境変数読み込み**
```python
# app/core/config.py
from .constants import DEFAULT_OPENAI_MODEL, DEFAULT_DATABASE_URL

class Settings:
    # 統一パターン: os.getenv(key, default)
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    DATABASE_URL: str = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
```

#### **3. アプリケーションコードで使用**
```python
# app/clients.py
from .core.config import settings

# 環境変数またはデフォルト値を自動選択
model=settings.OPENAI_MODEL
```

**このパターンのメリット**:
- ✅ デフォルト値の一元管理（constants.py）
- ✅ 環境変数未設定時の安全なフォールバック
- ✅ FastAPIコミュニティ標準に準拠
- ✅ 今後の環境変数追加時の一貫性確保

### ⚠️ **重要: 環境変数追加時のcompose.yaml更新**

**環境変数を新規追加する際は、必ずcompose.yamlも更新すること**

```yaml
# compose.yaml - fastapiサービスのenvironmentセクション
environment:
  DATABASE_URL: ${DATABASE_URL}
  OPENAI_API_KEY: ${OPENAI_API_KEY}
  OPENAI_MODEL: ${OPENAI_MODEL}
  JWT_SECRET_KEY: ${JWT_SECRET_KEY}
  JWT_ACCESS_TOKEN_EXPIRE_MINUTES: ${JWT_ACCESS_TOKEN_EXPIRE_MINUTES}
  # ← 新しい環境変数はここに追加
```

**理由**: Docker環境では2段階設定が必要
1. `.env`ファイルからDocker Compose変数置換
2. `environment`セクションで明示的にコンテナに変数を渡す

**忘れた場合の症状**: Docker環境でのみ環境変数が反映されず、デフォルト値が使用される

### 📝 **実装済み環境変数一覧**

現在このパターンで実装済みの環境変数：

| 環境変数 | デフォルト値（constants.py） | 設定場所 |
|---------|---------------------------|---------|
| `OPENAI_MODEL` | `"gpt-4o"` | `config.py:48` |
| `OPENAI_MAX_TOKENS` | `1024` | `config.py:49` |
| `OPENAI_TEMPERATURE` | `0.7` | `config.py:50` |
| `DATABASE_URL` | `"postgresql+psycopg://chatuser:chatpassword@localhost:5432/chatdb"` | `config.py:53` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | `config.py:56` |

**従来の`DATABASE_URL_FALLBACK`は不要** - constants.pyパターンにより、環境変数未設定時は自動的にデフォルト値が使用される設計に統一。

### 🚫 **環境変数化対応不要の判定**

以下の環境変数は検討の結果、環境変数化を行わないことに決定：

#### **FASTAPI_HOST/FASTAPI_PORT (app/main.py)**
- **判定理由**: 開発環境では固定値（0.0.0.0:8000）が適切
- **本番環境**: uvicornコマンドライン引数で直接指定
- **Docker環境**: compose.yamlでポートマッピング管理
- **FastAPI公式**: 環境変数化推奨だが、プロジェクト特性上不要

#### **DOCKER_EXPOSE_PORT (Dockerfile)**
- **判定理由**: プロジェクト内で8000ポート統一
- **管理方針**: compose.yamlでのポートマッピングで十分
- **過度な抽象化回避**: 実際の変更需要が低い設定

**この判定により、3項目の環境変数化タスクが完了扱いとなった。**

## 🔐 **JWT_SECRET_KEY必須環境変数化の実装**

セキュリティ上重要なJWT_SECRET_KEYを必須環境変数として実装。未設定時はアプリケーション起動を停止。

### **実装概要**

#### **1. 必須環境変数チェック関数の追加**
```python
# app/core/config.py
def validate_required_env(key: str) -> str:
    """必須環境変数を検証・取得（未設定時はValueErrorを発生）"""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"{key} environment variable is required")
    return value

def validate_optional_env(key: str, default: str) -> str:
    """オプション環境変数を検証・取得（未設定時はデフォルト値を使用）"""
    return os.getenv(key, default)
```

#### **2. JWT_SECRET_KEYの必須化**
```python
# app/core/config.py - Settings class
JWT_SECRET_KEY: str = validate_required_env("JWT_SECRET_KEY")
```

#### **3. security.pyの修正**
```python
# app/core/security.py
from .config import settings

JWT_SECRET_KEY = settings.JWT_SECRET_KEY  # 必須環境変数から取得
```

### **🔑 強力なJWTシークレットキー生成方法**

#### **方法1: Python secretsモジュール使用（推奨）**
```bash
# 512bit（64文字）の暗号学的に安全なランダムキー生成
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# 出力例:
# P9EIUv7pGSL2ymBWXMNl5XGmmNmzxhdDRFpfo6t7RMbojvG9fV4xaWQyywRPZL5iiNU_6-_q9zFsJ5wAurJKfw
```

#### **方法2: OpenSSLコマンド使用**
```bash
# 512bit（64バイト）のランダムキー生成
openssl rand -base64 64

# hex形式での生成
openssl rand -hex 32
```

#### **方法3: Pythonワンライナー（開発用）**
```bash
python3 -c "import os; print(os.urandom(64).hex())"
```

### **🛡️ セキュリティ要件**

| 要件 | 推奨値 | 理由 |
|------|--------|------|
| **最小長** | 512bit (64文字) | JWT標準推奨、ブルートフォース攻撃耐性 |
| **文字種** | Base64/URL-safe文字 | 環境変数での安全な使用 |
| **生成方法** | 暗号学的乱数生成器 | 予測不可能性の確保 |
| **環境別** | 環境ごとに異なるキー | 環境間での認証分離 |

### **⚠️ セキュリティリスク**

- **未設定時**: アプリケーション起動停止により事故防止
- **弱いキー使用時**: JWT偽造による認証迂回の重大リスク
- **キー漏洩時**: 全ユーザーセッションの無効化が必要