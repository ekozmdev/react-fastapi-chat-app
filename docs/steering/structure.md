# プロジェクト構造（Structure）

## ディレクトリ構成

### プロジェクト全体構造

```
react-fastapi-chat-app/
├── frontend/                 # React フロントエンド
├── backend/                  # FastAPI バックエンド
├── nginx/                    # Nginx 設定
├── docs/                     # プロジェクト文書
│   ├── steering/             # ステアリングファイル
│   ├── requirements.md       # 要件定義
│   ├── design.md            # 設計書
│   └── api-design.md        # API 仕様書
├── compose.yaml             # Docker Compose 設定
├── CLAUDE.md                # Claude Code 用設定
├── AGENTS.md               # 一般 AI エージェント用設定
├── GEMINI.md               # Gemini 用設定
└── README.md               # プロジェクト概要
```

### フロントエンド構造

```
frontend/
├── src/                     # ソースコード
│   ├── auth/                # 認証関連コンポーネント
│   │   ├── AuthContext.tsx  # 認証状態管理
│   │   ├── LoginRoute.tsx   # ログインルート
│   │   └── ProtectedRoute.tsx # 保護されたルート
│   ├── pages/               # ページコンポーネント
│   │   ├── Chat.tsx         # メインチャットページ
│   │   ├── Login.tsx        # ログインページ
│   │   └── NotFound.tsx     # 404 エラーページ
│   ├── styles/              # スタイルシート
│   │   ├── App.css          # アプリケーション全体スタイル
│   │   └── index.css        # グローバルスタイル
│   ├── App.tsx              # ルーティング定義
│   ├── main.tsx             # エントリーポイント
│   ├── types.ts             # TypeScript 型定義
│   └── utils.ts             # ユーティリティ関数
├── public/                  # 公開ファイル
├── dist/                    # ビルド出力（Git 管理外）
├── node_modules/            # 依存関係（Git 管理外）
├── package.json             # npm 設定
├── tsconfig.json           # TypeScript 設定
├── vite.config.ts          # Vite 設定
├── biome.json              # Biome 設定
├── Dockerfile              # Docker 設定
└── index.html              # HTML テンプレート
```

### バックエンド構造

```
backend/
├── app/                     # アプリケーションコード
│   ├── core/                # コア機能層
│   │   ├── config.py        # 設定管理
│   │   ├── constants.py     # 定数定義
│   │   ├── deps.py          # 依存注入
│   │   ├── security.py      # セキュリティ機能
│   │   └── utils.py         # ユーティリティ
│   ├── db/                  # データベース層
│   │   └── session.py       # DB セッション管理
│   ├── models/              # データモデル層
│   │   ├── __init__.py      # モデルエクスポート
│   │   ├── base.py          # ベースモデル
│   │   ├── user.py          # ユーザーモデル
│   │   └── conversation.py  # 会話・メッセージモデル
│   ├── schemas/             # データ検証層
│   │   ├── __init__.py      # スキーマエクスポート
│   │   ├── auth.py          # 認証スキーマ
│   │   └── common.py        # 共通スキーマ
│   ├── clients.py           # 外部API統合
│   ├── tools.py             # ツール定義
│   ├── helper.py            # ビジネスロジック補助
│   └── main.py              # FastAPI アプリ・ルート定義
├── alembic/                 # データベースマイグレーション
│   ├── versions/            # マイグレーションファイル
│   ├── env.py               # Alembic 環境設定
│   └── script.py.mako       # マイグレーションテンプレート
├── scripts/                 # 管理スクリプト
│   └── manage_users.py      # ユーザー管理
├── tests/                   # テストファイル（将来追加）
├── pyproject.toml           # Python 依存関係・設定
├── requirements.txt         # 本番用依存関係
├── requirements_dev.txt     # 開発用依存関係
├── uv.lock                  # uv ロックファイル
├── alembic.ini              # Alembic 設定
├── Dockerfile               # Docker 設定
└── init_db.py               # DB 初期化スクリプト
```

## 命名規則

### ファイル・ディレクトリ命名

**フロントエンド**
```
# React コンポーネント: PascalCase
Chat.tsx
LoginRoute.tsx
ProtectedRoute.tsx
NotFound.tsx

# TypeScript ファイル: camelCase
types.ts
utils.ts

# CSS ファイル: kebab-case または PascalCase
App.css
index.css

# ディレクトリ: kebab-case
auth/
pages/
styles/
```

**バックエンド**
```python
# Python モジュール・パッケージ: snake_case
models/
schemas/
core/
user.py
conversation.py

# クラス: PascalCase
class User(Base):
class ConversationCreate(BaseModel):

# 関数・変数: snake_case
def get_current_user():
user_id = "user_123"

# 定数: UPPER_SNAKE_CASE
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
JWT_SECRET_KEY = "secret"
```

### データベース命名

```sql
-- テーブル: snake_case (複数形)
users
conversations
messages

-- カラム: snake_case
user_id
created_at
updated_at

-- インデックス: idx_[テーブル名]_[カラム名]
idx_messages_conversation_created
idx_conversations_user_updated

-- 外部キー制約: [テーブル名]_[カラム名]_fkey
messages_conversation_id_fkey
conversations_user_id_fkey
```

### API エンドポイント命名

```
# リソース: 複数形 + kebab-case
/api/conversations
/api/auth/login

# パスパラメータ: snake_case
/api/conversations/{conversation_id}

# クエリパラメータ: snake_case
?skip=0&limit=20
?user_id=123
```

## アーキテクチャ原則

### レイヤー分離原則

**フロントエンド層分離**
```
Presentation Layer (Components)
├── pages/ (ルーティング単位)
├── auth/ (認証UI)
└── styles/ (視覚表現)

Business Logic Layer
├── Context API (状態管理)
├── Custom Hooks (ロジック再利用)
└── utils.ts (共通処理)

Communication Layer
├── SSE Client (リアルタイム通信)
├── API Calls (REST通信)
└── types.ts (データ契約)
```

**バックエンド層分離**
```
Presentation Layer
└── main.py (FastAPI ルート・エンドポイント)

Business Logic Layer
├── helper.py (ビジネスロジック)
├── tools.py (ツール実行)
└── clients.py (外部API統合)

Data Access Layer
├── models/ (データモデル)
├── schemas/ (データ検証)
└── db/ (データベース接続)

Infrastructure Layer
└── core/ (設定・セキュリティ・共通機能)
```

### 依存関係原則

**フロントエンド依存関係**
```typescript
// 上位層が下位層に依存 (逆依存禁止)
pages/Chat.tsx
  ↓ (import)
auth/AuthContext.tsx
  ↓ (import)
utils.ts

// 型定義は最下位層
types.ts (どの層からも参照可能)
```

**バックエンド依存関係**
```python
# main.py (最上位層)
from .helper import process_message
from .core.deps import get_current_user
from .schemas.common import ChatRequest

# helper.py (ビジネスロジック層)
from .models import User, Conversation
from .clients import get_chat_agent

# core層は他の層に依存しない
# models層は base.py のみに依存
```

## インポート・参照方針

### フロントエンド インポート

```typescript
// 相対インポート (同一ディレクトリ・近接ディレクトリ)
import { AuthContext } from './AuthContext';
import LoginRoute from '../auth/LoginRoute';

// 絶対インポート (遠い関係・外部ライブラリ)
import React from 'react';
import { Navigate } from 'react-router-dom';
import type { Message } from '../types';

// インポート順序
// 1. React・外部ライブラリ
// 2. 内部コンポーネント
// 3. 型定義
// 4. CSS
```

### バックエンド インポート

```python
# 標準ライブラリ
from datetime import datetime
import json

# 外部ライブラリ
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

# アプリケーション内部
from .core.config import settings
from .models import User
from .schemas.auth import LoginRequest

# 相対インポート使用 (同一パッケージ内)
from .helper import process_message
from ..models.user import User  # 上位階層参照時
```

## ファイル内構造ガイドライン

### React コンポーネント構造

```typescript
// imports (外部 → 内部の順)
import React from 'react';
import { useState } from 'react';
import type { ComponentProps } from './types';

// type definitions (コンポーネント固有)
interface LocalState {
  // ...
}

// main component
const ComponentName: React.FC<ComponentProps> = ({ props }) => {
  // state declarations
  const [state, setState] = useState<LocalState>();
  
  // handlers (useCallback推奨)
  const handleAction = useCallback(() => {
    // ...
  }, [dependencies]);
  
  // effects
  useEffect(() => {
    // ...
  }, [dependencies]);
  
  // render helpers (必要な場合)
  const renderSubComponent = () => {
    // ...
  };
  
  // main render
  return (
    <div>
      {/* JSX */}
    </div>
  );
};

export default ComponentName;
```

### Python モジュール構造

```python
"""モジュール説明（docstring）"""

# imports
from datetime import datetime
from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from .core.config import settings

# constants
DEFAULT_LIMIT = 20

# type definitions
UserID = str

# functions (public → private の順)
def public_function(param: str) -> dict:
    """公開関数の説明"""
    return _private_function(param)

def _private_function(param: str) -> dict:
    """プライベート関数（アンダースコア接頭辞）"""
    pass

# classes
class ClassName:
    """クラス説明"""
    
    def __init__(self, param: str):
        self.param = param
    
    def public_method(self) -> str:
        """公開メソッド"""
        return self._private_method()
    
    def _private_method(self) -> str:
        """プライベートメソッド"""
        pass
```

この構造ガイドラインに従うことで、プロジェクトの一貫性と保守性を保ちます。