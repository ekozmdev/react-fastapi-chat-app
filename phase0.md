# Phase 0: モデル定義の分割とアーキテクチャ整理

## 概要

現在のmain.pyにDBモデル、認証ロジック、FastAPIエンドポイントが混在している状況を改善し、Phase 1/2の実装に向けて保守性の高い構造に整理します。

## 現状分析

### 現在の問題点
1. **main.pyの肥大化**: 600行超でモデル定義、認証、エンドポイントが混在
2. **関心事の分離不足**: DBモデルとAPIロジックが同一ファイル
3. **拡張性の問題**: Phase 1/2でのツールモデル追加時の影響範囲が大きい
4. **テスタビリティ**: 単体テストでの依存関係が複雑

### 影響するファイル分析

#### 1. **Alembic設定** (`/backend/alembic/env.py`)
**現在の設定:**
```python
# line 14
from app.main import Base
# line 33  
target_metadata = Base.metadata
```

**影響:**
- モデル分割後はインポートパスの変更が必要
- Baseの参照方法を変更

#### 2. **既存マイグレーション** (`ef9a841e5b1a_add_users_table_and_user_id_to_.py`)
**影響評価:**
- ✅ **影響なし**: 既存マイグレーションは純粋なSQLAlchemy操作
- マイグレーション履歴は保持される
- テーブル構造は変更されない

#### 3. **ユーザー管理スクリプト** (`/backend/scripts/manage_users.py`)
**現在の設定:**
```python
# line 21
from app.main import User
```

**影響:**
- Userモデルのインポートパス変更が必要
- ⚠️ **重要**: 運用中のユーザー管理に影響する可能性

#### 4. **データベース初期化スクリプト** (`/backend/init_db.py`)
**現在の設定:**
```python
# line 12
from app.main import Base
```

**影響:**
- Baseのインポートパス変更が必要
- 新規環境セットアップ時の影響

#### 5. **main.pyでのモデル使用箇所**
**確認が必要な箇所:**
- エンドポイント内でのモデル参照
- リレーション操作
- データベースクエリ

## 提案する新構造

### ディレクトリ構造
```
/backend/app/
├── __init__.py
├── main.py              # FastAPIアプリとエンドポイント（軽量化）
├── database.py          # DB接続設定
├── auth.py              # 認証関連
├── schemas.py           # Pydanticスキーマ
└── models/              # データベースモデル
    ├── __init__.py      # 全モデルのエクスポート
    ├── base.py          # Base設定
    ├── user.py          # Userモデル
    ├── conversation.py  # Conversation、Messageモデル
    └── tool.py          # 将来のToolExecutionモデル（Phase1/2用）
```

### 実装詳細

#### 1. `/app/models/base.py`
```python
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
```

#### 2. `/app/models/__init__.py`
```python
from .base import Base
from .user import User
from .conversation import Conversation, Message

__all__ = ["Base", "User", "Conversation", "Message"]
```

#### 3. `/app/database.py`
```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://chatuser:chatpassword@localhost:5432/chatdb"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### 4. `/app/models/user.py`
```python
import uuid
from datetime import UTC, datetime
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    # リレーション
    conversations = relationship("Conversation", back_populates="user")
```

#### 5. `/app/models/conversation.py`
```python
import uuid
from datetime import UTC, datetime
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from .base import Base

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

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
    
    # リレーション
    conversation = relationship("Conversation", back_populates="messages")
```

#### 6. `/app/auth.py`
```python
import os
from datetime import UTC, datetime, timedelta
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .models import User

# JWT設定
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
)

# パスワードハッシュ化
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT認証
security = HTTPBearer()

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
```

## 変更による影響分析

### 1. **Alembic設定の変更**

#### 修正が必要: `/backend/alembic/env.py`
```python
# 変更前
from app.main import Base

# 変更後
from app.models import Base
```

### 2. **ユーザー管理スクリプトの変更**

#### 修正が必要: `/backend/scripts/manage_users.py`
```python
# 変更前
from app.main import User

# 変更後
from app.models import User
```

### 3. **データベース初期化スクリプトの変更**

#### 修正が必要: `/backend/init_db.py`
```python
# 変更前
from app.main import Base

# 変更後
from app.models import Base
```

### 4. **main.pyの変更**

#### インポートの変更
```python
# 変更前
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# 変更後
from .models import Base, User, Conversation, Message
from .database import get_db
from .auth import (
    security, verify_password, get_password_hash, 
    create_access_token, verify_token, authenticate_user
)
```

### 3. **既存のマイグレーションへの影響**

**評価結果: ✅ 影響なし**
- 既存のマイグレーションファイルは変更不要
- テーブル構造は同一
- マイグレーション履歴は保持される

### 4. **Phase 1/2への準備**

#### Phase 1での利点
```python
# /app/models/tool.py として追加可能
class ToolMetadata(Base):
    __tablename__ = "tool_metadata"
    # Phase 1用の軽量モデル
```

#### Phase 2での利点
```python
# /app/models/tool.py に追加
class ToolExecution(Base):
    __tablename__ = "tool_executions"
    # Phase 2用の詳細モデル
```

## リスク評価

### 低リスク
- **既存データ**: 変更されない
- **マイグレーション履歴**: 保持される
- **API動作**: 変更されない

### 中リスク
- **インポート文の変更**: 5つのファイルで調整が必要
- **スクリプト依存**: 運用スクリプトの動作に影響
- **テスト**: モックやフィクスチャの調整が必要

### 高リスク
- **運用スクリプト**: `manage_users.py`が動作しなくなる可能性
- **新規環境構築**: `init_db.py`が動作しなくなる可能性

### 対策
1. **段階的実装**: 一度にすべて変更せず、段階的に移行
2. **スクリプト事前テスト**: 運用スクリプトの動作確認を優先
3. **テスト実行**: 各段階でテスト実行して動作確認
4. **ロールバック計画**: 問題発生時の復旧手順
5. **バックアップ作成**: 変更前のファイルバックアップ

## 実装手順（修正版）

### Step 1: 事前準備
1. 現在の動作確認とバックアップ作成
2. 運用スクリプトの動作テスト実施
3. 変更対象ファイルのバックアップ

### Step 2: モデルファイルの作成
1. `/app/models/` ディレクトリ作成
2. `base.py`, `user.py`, `conversation.py` 作成
3. `/app/models/__init__.py` 作成

### Step 3: 補助ファイルの作成
1. `/app/database.py` 作成
2. `/app/auth.py` 作成

### Step 4: 設定・スクリプトファイルの更新
1. `/alembic/env.py` のインポート変更
2. `/scripts/manage_users.py` のインポート変更
3. `/init_db.py` のインポート変更
4. 各スクリプトの動作確認

### Step 5: main.pyの大幅軽量化
1. モデル定義の削除
2. 認証ロジックの移動
3. データベース設定の移動
4. インポート文の更新

### Step 6: 動作確認
1. Alembicの動作確認: `alembic check`
2. 運用スクリプトの動作確認
3. アプリケーションの起動確認
4. API動作確認
5. 既存機能のリグレッションテスト

### Step 7: Phase 1準備
1. `/app/models/tool.py` の準備
2. Phase 1実装に向けたベース確立

## 成功の指標

### 完了確認項目
- [ ] Alembicが正常動作（`alembic check`）
- [ ] 既存APIが正常動作
- [ ] 認証機能が正常動作
- [ ] モデル間のリレーションが正常動作
- [ ] **運用スクリプトが正常動作**（`manage_users.py`）
- [ ] **DB初期化スクリプトが正常動作**（`init_db.py`）
- [ ] テストが全て通過
- [ ] Phase 1実装の準備完了

### 重要な検証項目
- [ ] `python scripts/manage_users.py list` でユーザー一覧表示
- [ ] `alembic current` でマイグレーション状態確認
- [ ] FastAPIアプリケーション起動確認
- [ ] 認証付きAPI呼び出しテスト
- [ ] 新規ユーザー登録・ログインテスト

## Phase 1/2との連携

### Phase 1での活用
- `tool_metadata` カラムを `Message` モデルに追加
- 軽量なツール情報を JSON で保存

### Phase 2での活用
- `ToolExecution` モデルを独立ファイルで追加
- 詳細なツール実行履歴を関連テーブルで管理

この Phase 0 により、安全で保守性の高いアーキテクチャを確立し、Phase 1/2での機能拡張を円滑に進められます。