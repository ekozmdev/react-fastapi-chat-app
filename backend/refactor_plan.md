# FastAPI バックエンド リファクタリング計画

## 現在の構造
```
backend/app/
├── __init__.py
├── main.py                           # 703行 - 全ての機能が集約
├── auth.py                          # 認証ロジック（JWT、パスワード）
├── database.py                      # DB接続設定
├── models/                          # SQLAlchemyモデル
│   ├── __init__.py
│   ├── base.py
│   ├── conversation.py
│   ├── tool_execution.py
│   └── user.py
├── tools.py                         # ツール定義（現状維持）
├── tool_execution_manager.py        # ツール実行管理（現状維持）
└── enhanced_streaming.py           # デッドコード（削除対象）
```

## 目標構造（軽いリファクタリング）
```
backend/app/
├── __init__.py
├── main.py                          # 全エンドポイント維持（軽微な整理のみ）
├── core/                           # 設定・共通機能
│   ├── __init__.py
│   ├── config.py                   # アプリケーション設定
│   ├── deps.py                     # 共通依存性（get_current_user等）
│   └── security.py                 # JWT認証・パスワードハッシュ（auth.pyから移行）
├── db/                            # データベース関連
│   ├── __init__.py
│   └── session.py                  # DB接続設定（database.pyから移行）
├── schemas/                       # Pydanticモデル（入出力）
│   ├── __init__.py
│   ├── auth.py                     # LoginRequest, Token, UserResponse等
│   ├── conversation.py             # ChatRequest, ConversationResponse等
│   └── common.py                   # 共通スキーマ（SSEEvent等）
├── models/                        # SQLAlchemyモデル（現状維持）
│   ├── __init__.py
│   ├── base.py
│   ├── conversation.py
│   ├── tool_execution.py
│   └── user.py
├── tools.py                       # ツール定義（現状維持）
├── tool_execution_manager.py      # ツール実行管理（現状維持）
└── utils/                         # 汎用ユーティリティ（必要に応じて）
    └── __init__.py
```

## 移行方針（軽量版）

### フェーズ1: 基盤設定分離（core/）
- [ ] `core/config.py` - 環境変数・設定管理
- [ ] `core/security.py` - `auth.py`の内容を移行
- [ ] `core/deps.py` - `get_current_user`等の共通依存性
- [ ] `db/session.py` - `database.py`の内容を移行

### フェーズ2: スキーマ分離（schemas/）
- [ ] `schemas/auth.py` - 認証関連Pydanticモデル
- [ ] `schemas/conversation.py` - 会話関連Pydanticモデル  
- [ ] `schemas/common.py` - SSEEvent等の共通スキーマ

### フェーズ3: main.py軽微な整理
- [ ] 分離したファイルからのimportに変更
- [ ] 不要ファイル削除（enhanced_streaming.py等）

## 非対象（現状維持）
- `main.py`のエンドポイント定義 - そのまま残す
- `tools.py` - ツール定義
- `tool_execution_manager.py` - ツール実行管理  
- `models/` - SQLAlchemyモデル
- SSEストリーミングロジック - main.pyに残す
- APIルーター分離 - 行わない

## 期待効果
- コードの整理・可読性向上
- 設定とスキーマの分離による責任明確化
- 新機能追加時の影響範囲限定
- main.pyの長大さは許容（エンドポイントはそのまま）