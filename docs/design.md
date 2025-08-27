# 設計書

## システムアーキテクチャ

### 全体構成

このシステムは、OpenAI Agent SDK でのツール実行を可視化するための3層アーキテクチャを採用しています。

```
フロントエンド層 (React + TypeScript)
├── UI Components (チャットインターフェース、ツール表示)
├── State Management (認証状態、チャット状態)
└── SSE Client (リアルタイム通信)
                    ↕ HTTP/SSE
バックエンド層 (FastAPI + Python)
├── API Routes (認証、チャット、SSE)
├── Business Logic (イベントハンドラー、ツール処理)
├── Agent Client (OpenAI Agent SDK統合)
└── Tool Definitions (利用可能ツール)
                    ↕ SQL
データベース層 (PostgreSQL)
├── Users (ユーザー情報)
├── Conversations (会話セッション)
└── Messages (メッセージ、ツール実行記録)
```

### 設計原則

1. **ツール実行中心設計**: ツール実行を第一級市民として扱う
2. **イベント駆動**: リアルタイム性重視のイベント処理
3. **責任分離**: 各層の明確な責任分担
4. **拡張性**: 新しいツールの容易な追加

## データフローと処理の流れ

### ツール実行フロー

```
1. ユーザーメッセージ送信
   ├── フロントエンド: SSEリクエスト開始
   └── バックエンド: ユーザーメッセージDB保存

2. Agent実行開始
   ├── OpenAI Agent SDK: run_streamed() 実行
   └── ツール実行判定

3. ツール実行段階
   ├── tool_called イベント → フロントエンド: スピナー表示
   ├── ツール実行 (get_current_time, calculate, web_search)
   └── tool_output イベント → DB保存 + フロントエンド結果表示

4. AI応答段階
   ├── text_delta イベント → フロントエンド: ストリーミング表示
   └── done イベント → 完了処理
```

### データベース設計

#### テーブル構造

**users テーブル**
```sql
- id: String (UUID-like) PRIMARY KEY
- email: String UNIQUE
- username: String UNIQUE
- password_hash: String
- is_active: Boolean
- created_at: DateTime
- updated_at: DateTime
```

**conversations テーブル**
```sql
- id: String (UUID-like) PRIMARY KEY
- title: String
- user_id: String FOREIGN KEY → users.id
- created_at: DateTime
- updated_at: DateTime
```

**messages テーブル**
```sql
- id: String (UUID-like) PRIMARY KEY
- conversation_id: String FOREIGN KEY → conversations.id
- role: String ('user', 'assistant', 'tool')
- content: Text (ツールの場合はJSON文字列)
- created_at: DateTime
```

#### 統一メッセージモデル

ツール実行記録も通常メッセージも同一テーブルで管理:

```json
// 通常メッセージ
{
  "role": "user",
  "content": "現在時刻を教えて"
}

// ツール実行記録
{
  "role": "tool", 
  "content": "{\"tool_call_id\": \"call_123\", \"tool_name\": \"get_current_time\", \"output\": \"2025-01-15 10:30:00 UTC\", \"status\": \"success\"}"
}

// AI応答
{
  "role": "assistant",
  "content": "現在の時刻は2025年1月15日10時30分です。"
}
```

## フロントエンド設計

### コンポーネント階層

```
App
├── AuthProvider (認証状態管理)
├── Router (ルーティング管理)
└── Chat (メイン画面)
    ├── Sidebar (会話履歴)
    ├── MessageList (メッセージ表示)
    │   ├── UserMessage
    │   ├── AssistantMessage
    │   └── ToolIndicator (ツール実行表示)
    ├── InputArea (入力エリア)
    └── ToolSidebar (ツール詳細表示)
```

### 状態管理

**認証状態 (Context API)**
```typescript
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
```

**チャット状態 (ローカル状態)**
```typescript
const [messages, setMessages] = useState<Message[]>();
const [streamingMessage, setStreamingMessage] = useState<StreamingMessage>();
const [conversations, setConversations] = useState<Conversation[]>();
const [toolExecutionState, setToolExecutionState] = useState<ToolState>();
```

### SSEクライアント設計

**イベント処理パターン**
```typescript
// SSEイベント分岐処理
switch (data.role) {
  case 'tool':
    // ツール実行結果表示
    displayToolResult(data);
    break;
  case 'assistant':
    // AI応答ストリーミング
    updateStreamingMessage(data);
    break;
}

// イベント完了処理
if (eventType === 'done') {
  finalizeMessage();
  updateConversations();
}
```

### ツール実行UI設計

**視覚的フィードバック**
- スピナーアニメーション: ツール実行中表示
- プログレスインジケーター: 実行状況表示
- 結果ボタン: 「🔧 ツール実行結果」

**結果表示方式**
- インライン表示: チャットフロー内統合
- サイドバー表示: 詳細情報専用エリア
- Markdownレンダリング: 構造化コンテンツ対応

## バックエンド設計

### レイヤード構造

```
app/
├── core/ (コア機能)
│   ├── config.py (設定管理)
│   ├── security.py (認証・セキュリティ)
│   ├── deps.py (依存注入)
│   └── utils.py (共通ユーティリティ)
├── models/ (データモデル)
│   ├── user.py
│   ├── conversation.py
│   └── base.py
├── schemas/ (データ検証)
│   ├── auth.py
│   └── common.py
├── db/ (データベース層)
│   └── session.py
├── clients.py (外部API統合)
├── tools.py (ツール定義)
├── helper.py (ビジネスロジック)
└── main.py (APIエンドポイント)
```

### API エンドポイント設計

**認証API**
```python
POST /api/auth/login      # ログイン
POST /api/auth/refresh    # トークンリフレッシュ  
GET  /api/auth/me         # ユーザー情報取得
```

**会話API**
```python
GET    /api/conversations              # 会話一覧
GET    /api/conversations/{id}         # 会話詳細
DELETE /api/conversations/{id}         # 会話削除
```

**ストリーミングAPI**
```python
POST /api/chat/stream                  # SSEチャット
```

## API仕様詳細

### 認証システム

**認証方式**: JWT (JSON Web Token)
- トークン形式: Bearer Token
- 有効期限: 30分 (1800秒)
- リフレッシュ: `/api/auth/refresh`エンドポイントで更新可能

**認証ヘッダー**
```http
Authorization: Bearer <JWT_TOKEN>
```

### 認証エンドポイント

**1. ユーザーログイン**
```
POST /api/auth/login
```
**リクエスト**:
```json
{
  "email": "user@example.com", 
  "password": "password123"
}
```

**レスポンス** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**2. トークンリフレッシュ**
```
POST /api/auth/refresh (認証必須)
```
**レスポンス** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer", 
  "expires_in": 1800
}
```

**3. 現在のユーザー情報取得**
```
GET /api/auth/me (認証必須)
```
**レスポンス** (200):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "username": "username",
  "is_active": true,
  "created_at": "2025-08-23T12:00:00Z"
}
```

### 会話管理エンドポイント

**1. 会話一覧取得**
```
GET /api/conversations?skip=0&limit=20 (認証必須)
```
**レスポンス** (200):
```json
{
  "conversations": [
    {
      "id": "conv_123e4567-e89b-12d3-a456-426614174000",
      "title": "ChatGPTについて教えて",
      "created_at": "2025-08-23T12:00:00Z",
      "updated_at": "2025-08-23T12:30:00Z",
      "message_count": 5
    }
  ]
}
```

**2. 特定会話の詳細取得**
```
GET /api/conversations/{conversation_id} (認証必須)
```
**レスポンス** (200):
```json
{
  "conversation": {
    "id": "conv_123e4567-e89b-12d3-a456-426614174000",
    "title": "ChatGPTについて教えて",
    "created_at": "2025-08-23T12:00:00Z",
    "updated_at": "2025-08-23T12:30:00Z"
  },
  "messages": [
    {
      "id": "msg_789e0123-e89b-12d3-a456-426614174222",
      "role": "user",
      "content": "ChatGPTについて教えてください",
      "timestamp": "2025-08-23T12:00:00Z"
    },
    {
      "id": "msg_abc1234d-e89b-12d3-a456-426614174333", 
      "role": "assistant",
      "content": "ChatGPTは、OpenAIが開発した大規模言語モデルです...",
      "timestamp": "2025-08-23T12:00:30Z"
    },
    {
      "id": "msg_def5678e-e89b-12d3-a456-426614174444",
      "role": "tool",
      "content": "{\"tool_call_id\": \"call_123\", \"tool_name\": \"get_current_time\", \"output\": \"2025-08-23 12:00:45 UTC\", \"status\": \"success\"}",
      "timestamp": "2025-08-23T12:00:45Z"
    }
  ]
}
```

### ストリーミングチャットAPI

**SSEストリーミングチャット**
```
POST /api/chat/stream (認証必須)
```

**リクエスト**:
```json
{
  "conversation_id": "conv_123e4567-e89b-12d3-a456-426614174000",  // 空文字で新規作成
  "message": "こんにちは！今日はどんな一日でしたか？"
}
```

**レスポンス形式**: `Content-Type: text/event-stream`

**新規チャット作成時の応答**
```http
data: {"type": "conversation_created", "conversation_id": "conv_789e0123-e89b-12d3-a456-426614174000", "timestamp": "2025-08-23T12:00:00Z"}

data: {"role": "assistant", "content": "こんにちは！", "id": "assistant_123"}

data: {"role": "assistant", "content": "初めまして。", "id": "assistant_123"}

event: done
data: {"id": "assistant_123"}
```

**ツール実行を含む応答**
```http
data: {"role": "tool", "content": "{\"tool_call_id\": \"call_abc123\", \"tool_name\": \"get_current_time\", \"output\": \"2025-08-23 12:00:45 UTC\", \"status\": \"success\"}", "id": "call_abc123", "timestamp": "2025-08-23T12:00:45Z"}

data: {"role": "assistant", "content": "現在の時刻は", "id": "assistant_456"}

data: {"role": "assistant", "content": "2025年8月23日", "id": "assistant_456"}

event: done  
data: {"id": "assistant_456"}
```

**利用可能ツール**:
- **get_current_time**: 現在時刻取得
- **calculate**: 数学計算実行（安全な式のみ）
- **web_search**: Web検索実行（Mock実装）

### データ形式・エラーハンドリング

**共通データ形式**
- 日時形式: ISO 8601 (UTC) - `2025-08-23T12:00:00Z`
- UUID形式: UUID4 - `123e4567-e89b-12d3-a456-426614174000`
- 文字エンコーディング: UTF-8
- JSON設定: `ensure_ascii=False` (日本語文字対応)

**エラーレスポンス形式**
```json
{
  "detail": "Error message description"
}
```

**主要HTTPステータスコード**
- `200`: 成功
- `401`: 認証エラー
- `404`: リソース未発見
- `422`: データ検証エラー
- `500`: サーバーエラー

### ツール統合設計

**ツール定義**
```python
@function_tool
def get_current_time() -> str:
    """現在時刻取得ツール"""
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

@function_tool  
def calculate(expression: str) -> str:
    """安全な計算ツール"""
    # 安全性チェック後、数式評価
    return f"{expression} = {result}"

@function_tool
def web_search(query: str, max_results: int = 5) -> str:
    """モックWeb検索ツール"""
    # モックデータ生成とMarkdown形式返却
    return markdown_results
```

**ツールリスト管理**
```python
AVAILABLE_TOOLS = [
    get_current_time,
    calculate,
    web_search,
]
```

### イベント処理設計

**統一イベントハンドラー**
```python
async def process_agent_events(agent, messages):
    async for event in agent.run_streamed(messages):
        if isinstance(event, RunItemStreamEvent):
            if event.name == "tool_called":
                yield create_tool_start_event(event)
            elif event.name == "tool_output":
                yield create_tool_result_event(event)
        elif isinstance(event, ResponseTextDeltaEvent):
            yield create_text_delta_event(event)
```

**SSE形式統一**
```python
# ツール実行開始
yield f"data: {json.dumps(tool_start_data)}\n\n"

# ツール実行結果
yield f"data: {json.dumps(tool_result_data)}\n\n"

# AI応答テキスト
yield f"data: {json.dumps(text_delta_data)}\n\n"

# 完了通知
yield f"event: done\ndata: {json.dumps(done_data)}\n\n"
```

## セキュリティ設計

### 認証・認可

**JWT実装**
```python
# トークン生成
def create_access_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": expire_time}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# トークン検証
def verify_token(token: str) -> str:
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return payload.get("sub")
```

**パスワードセキュリティ**
```python
# パスワードハッシュ化
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# パスワード検証
def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed)
```

### ツール実行セキュリティ

**計算ツールの安全性**
```python
def calculate(expression: str) -> str:
    # 許可文字のみチェック
    allowed_chars = set("0123456789+-*/.() ")
    if not all(c in allowed_chars for c in expression):
        return "エラー: 許可されていない文字"
    
    # 安全な評価実行
    result = eval(expression)  # 文字チェック済みのため安全
    return f"{expression} = {result}"
```

**入力検証**
```python
class ChatRequest(BaseModel):
    conversation_id: str = Field("", max_length=100)
    message: str = Field(..., min_length=1, max_length=10000)
    
    @field_validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('メッセージは空にできません')
        return v
```

## パフォーマンス設計

### フロントエンド最適化

**コンポーネント最適化**
```typescript
// メモ化でレンダリング最適化
const visibleMessages = useMemo(() => 
  messages.filter(msg => msg.role !== 'tool'), 
  [messages]
);

// コールバック最適化
const handleToolResult = useCallback((result: ToolResult) => {
  setSelectedToolMessages([result]);
  setRightSidebarOpen(true);
}, []);
```

**状態更新最適化**
```typescript
// バッチ更新による再レンダリング削減
setMessages(prev => [...prev, toolMessage]);
setStreamingMessage(null);
setIsLoading(false);
```

### バックエンド最適化

**データベース最適化**
```sql
-- インデックス設計
CREATE INDEX idx_messages_conversation_created 
ON messages(conversation_id, created_at);

CREATE INDEX idx_conversations_user_updated 
ON conversations(user_id, updated_at DESC);
```

**クエリ最適化**
```python
# N+1問題回避
conversations = db.query(Conversation)\
    .options(selectinload(Conversation.messages))\
    .filter(Conversation.user_id == user_id)\
    .all()
```

### ストリーミング最適化

**接続管理**
```python
class SSEConnectionManager:
    def __init__(self):
        self.connections = defaultdict(set)
    
    def add_connection(self, user_id: str, connection):
        self.connections[user_id].add(weakref.ref(connection))
    
    def cleanup_connections(self):
        # 切断された接続の自動クリーンアップ
        pass
```

## エラーハンドリング設計

### 階層化エラー処理

**カスタム例外**
```python
class ToolExecutionError(Exception):
    """ツール実行エラー"""
    pass

class StreamingError(Exception):
    """ストリーミングエラー"""
    pass

@app.exception_handler(ToolExecutionError)
async def tool_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": "ツール実行に失敗しました", "detail": str(exc)}
    )
```

**フロントエンドエラー処理**
```typescript
// SSEエラーハンドリング
const handleSSEError = useCallback((error: Error) => {
  console.error('SSE Error:', error);
  setIsLoading(false);
  setStreamingMessage(null);
  // ユーザー向けエラー表示
  showErrorMessage('接続エラーが発生しました。再試行してください。');
}, []);

// ツール実行エラー処理  
if (data.error) {
  setToolExecutionError(data.error);
  stopToolExecution();
}
```

## 拡張性設計

### 新しいツール追加

**ツール追加手順**
1. `tools.py` に新しいツール関数定義
2. `AVAILABLE_TOOLS` リストに追加
3. フロントエンドでツール結果表示コンポーネント追加（必要に応じて）

**ツール追加例**
```python
@function_tool
def file_operations(operation: str, filename: str) -> str:
    """ファイル操作ツール"""
    # ファイル操作ロジック
    return operation_result

# ツールリストに追加
AVAILABLE_TOOLS = [
    get_current_time,
    calculate, 
    web_search,
    file_operations,  # 新規追加
]
```

### UI拡張パターン

**ツール結果表示の拡張**
```typescript
const renderToolResult = (toolName: string, result: any) => {
  switch (toolName) {
    case 'get_current_time':
      return <TimeDisplay result={result} />;
    case 'calculate':
      return <CalculationResult result={result} />;
    case 'web_search':
      return <SearchResults result={result} />;
    case 'file_operations':
      return <FileOperationResult result={result} />;
    default:
      return <GenericToolResult result={result} />;
  }
};
```

この設計書に基づいて、OpenAI Agent SDK のツール実行を効果的に可視化し、開発者が理解しやすいUIシステムを構築することができます。