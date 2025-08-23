# API設計書

React FastAPI Chat Application のバックエンド API 設計仕様書

## 目次
- [認証システム](#認証システム)
- [認証エンドポイント](#認証エンドポイント)
- [会話管理エンドポイント](#会話管理エンドポイント)
- [ストリーミングチャットエンドポイント](#ストリーミングチャットエンドポイント)
- [共通仕様](#共通仕様)
- [エラーハンドリング](#エラーハンドリング)

---

## 認証システム

### 概要
- **認証方式**: JWT (JSON Web Token)
- **トークン形式**: Bearer Token
- **有効期限**: 30分 (1800秒)
- **リフレッシュ**: `/api/auth/refresh`エンドポイントで更新可能

### 認証ヘッダー
```http
Authorization: Bearer <JWT_TOKEN>
```

---

## 認証エンドポイント

### 1. ユーザーログイン

**エンドポイント**: `POST /api/auth/login`

**説明**: メールアドレスとパスワードでユーザー認証を行い、JWTアクセストークンを発行

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

**エラー**:
- `401`: 認証情報が無効またはアカウント無効
- `422`: リクエストデータ形式エラー

---

### 2. トークンリフレッシュ

**エンドポイント**: `POST /api/auth/refresh`

**説明**: 現在有効なトークンを使用して新しいアクセストークンを発行

**認証**: 必須

**レスポンス** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**エラー**:
- `401`: トークンが無効または期限切れ

---

### 3. 現在のユーザー情報取得

**エンドポイント**: `GET /api/auth/me`

**説明**: 認証されたユーザーの詳細情報を取得

**認証**: 必須

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

**エラー**:
- `401`: トークンが無効または期限切れ

---

### 4. ユーザー情報更新

**エンドポイント**: `PUT /api/auth/me`

**説明**: 認証されたユーザーのユーザー名やパスワードを更新

**認証**: 必須

**リクエスト**:
```json
{
  "username": "new_username",
  "current_password": "current_password",
  "new_password": "new_password"
}
```

**レスポンス** (200):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com", 
  "username": "new_username",
  "is_active": true,
  "created_at": "2025-08-23T12:00:00Z"
}
```

**エラー**:
- `400`: ユーザー名重複またはパスワード不一致
- `401`: トークンが無効または期限切れ
- `422`: リクエストデータ形式エラー

---

### 5. ログアウト

**エンドポイント**: `DELETE /api/auth/logout`

**説明**: ユーザーをログアウト（クライアント側でトークンを削除する必要がある）

**認証**: 必須

**レスポンス** (200):
```json
{
  "message": "Successfully logged out"
}
```

**エラー**:
- `401`: トークンが無効または期限切れ

---

## 会話管理エンドポイント

### 1. 新しい会話作成

**エンドポイント**: `POST /api/conversations`

**説明**: 認証されたユーザー用に新しい会話セッションを作成

**認証**: 必須

**レスポンス** (200):
```json
{
  "conversation_id": "conv_123e4567-e89b-12d3-a456-426614174000",
  "created_at": "2025-08-23T12:00:00Z",
  "updated_at": "2025-08-23T12:00:00Z"
}
```

**エラー**:
- `401`: トークンが無効または期限切れ

---

### 2. 会話一覧取得

**エンドポイント**: `GET /api/conversations`

**説明**: 認証されたユーザーの会話一覧を更新日時降順で取得

**認証**: 必須

**クエリパラメータ**:
- `skip` (int, optional): スキップする件数 (デフォルト: 0)
- `limit` (int, optional): 取得件数の上限 (デフォルト: 20)

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
    },
    {
      "id": "conv_456e7890-e89b-12d3-a456-426614174111",
      "title": "Pythonの基礎について",
      "created_at": "2025-08-22T15:30:00Z",
      "updated_at": "2025-08-22T16:00:00Z",
      "message_count": 3
    }
  ]
}
```

**エラー**:
- `401`: トークンが無効または期限切れ

---

### 3. 特定会話の詳細取得

**エンドポイント**: `GET /api/conversations/{conversation_id}`

**説明**: 指定された会話IDの会話情報と全メッセージ履歴を取得

**認証**: 必須

**パスパラメータ**:
- `conversation_id` (string): 取得する会話のID

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

**エラー**:
- `404`: 指定された会話が見つからない
- `401`: トークンが無効または期限切れ

---

### 4. 会話削除

**エンドポイント**: `DELETE /api/conversations/{conversation_id}`

**説明**: 指定された会話とその全メッセージを完全に削除

**認証**: 必須

**パスパラメータ**:
- `conversation_id` (string): 削除する会話のID

**レスポンス** (200):
```json
{
  "message": "deleted"
}
```

**エラー**:
- `404`: 指定された会話が見つからない
- `401`: トークンが無効または期限切れ

---

## ストリーミングチャットエンドポイント

### SSEストリーミングチャット

**エンドポイント**: `POST /api/chat/stream`

**説明**: Server-Sent Events (SSE) を使用してリアルタイムでAIチャット応答をストリーミング配信

**認証**: 必須（AuthorizationヘッダーでJWTトークン送信）

**リクエスト**:
```json
{
  "conversation_id": "conv_123e4567-e89b-12d3-a456-426614174000",
  "message": "こんにちは！今日はどんな一日でしたか？"
}
```

**新規チャット時のリクエスト**:
```json
{
  "conversation_id": "",
  "message": "初めてのメッセージです"
}
```

**レスポンス形式**: `Content-Type: text/event-stream`

#### 新規チャット作成時の応答

```http
data: {"type": "conversation_created", "conversation_id": "conv_789e0123-e89b-12d3-a456-426614174000", "timestamp": "2025-08-23T12:00:00Z"}

data: {"role": "assistant", "content": "こんにちは！", "id": "assistant_123"}

data: {"role": "assistant", "content": "初めまして。", "id": "assistant_123"}

event: done
data: {"id": "assistant_123"}

```

#### 通常のアシスタント応答

```http
data: {"role": "assistant", "content": "こんにちは！", "id": "assistant_123"}

data: {"role": "assistant", "content": "今日は", "id": "assistant_123"}

data: {"role": "assistant", "content": "とても良い", "id": "assistant_123"}

data: {"role": "assistant", "content": "一日でした。", "id": "assistant_123"}

event: done
data: {"id": "assistant_123"}

```

#### ツール実行を含む応答

```http
data: {"role": "tool", "content": "{\"tool_call_id\": \"call_abc123\", \"tool_name\": \"get_current_time\", \"output\": \"2025-08-23 12:00:45 UTC\", \"status\": \"success\"}", "id": "call_abc123", "timestamp": "2025-08-23T12:00:45Z"}

data: {"role": "assistant", "content": "現在の時刻は", "id": "assistant_456"}

data: {"role": "assistant", "content": "2025年8月23日", "id": "assistant_456"}

data: {"role": "assistant", "content": "12時00分45秒（UTC）", "id": "assistant_456"}

data: {"role": "assistant", "content": "です。", "id": "assistant_456"}

event: done
data: {"id": "assistant_456"}

```

#### エラー応答

```http
data: {"error": "エラーが発生しました: OpenAI API rate limit exceeded"}

```

**利用可能ツール**:
- **get_current_time**: 現在時刻取得
- **calculate**: 数学計算実行（安全な式のみ）
- **web_search**: Web検索実行（Mock実装）

**エラー**:
- `401`: トークンが無効または期限切れ
- `422`: リクエストデータ形式エラー

---

## 共通仕様

### データ形式
- **日時形式**: ISO 8601 (UTC) - `2025-08-23T12:00:00Z`
- **UUID形式**: UUID4 - `123e4567-e89b-12d3-a456-426614174000`
- **文字エンコーディング**: UTF-8
- **JSON設定**: `ensure_ascii=False` (日本語文字対応)

### HTTPヘッダー

#### リクエストヘッダー
```http
Content-Type: application/json
Authorization: Bearer <JWT_TOKEN>
Accept: application/json
```

#### レスポンスヘッダー (通常のAPI)
```http
Content-Type: application/json; charset=utf-8
```

#### レスポンスヘッダー (SSE)
```http
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
Access-Control-Allow-Origin: *
Access-Control-Allow-Headers: Authorization
```

### ページネーション
```json
{
  "skip": 0,
  "limit": 20,
  "total": 50
}
```

---

## エラーハンドリング

### エラーレスポンス形式

```json
{
  "detail": "Error message description"
}
```

### HTTPステータスコード

| コード | 説明 | 具体例 |
|--------|------|--------|
| `200` | 成功 | 正常なレスポンス |
| `201` | 作成成功 | リソース作成完了 |
| `400` | リクエストエラー | バリデーションエラー |
| `401` | 認証エラー | 無効なトークン |
| `403` | 権限エラー | アクセス権限なし |
| `404` | 未発見 | リソースが存在しない |
| `422` | データ検証エラー | Pydantic バリデーション失敗 |
| `429` | レート制限 | API呼び出し制限超過 |
| `500` | サーバーエラー | 内部処理エラー |

### 主要エラーメッセージ

#### 認証関連
```json
{"detail": "Incorrect email or password"}
{"detail": "Inactive user"}
{"detail": "Could not validate credentials"}
{"detail": "Token has expired"}
```

#### 会話関連
```json
{"detail": "Conversation not found"}
{"detail": "Access denied"}
```

#### データ検証
```json
{"detail": "Username already exists"}
{"detail": "Current password is required"}
{"detail": "Incorrect current password"}
```

---

## APIクライアント実装例

### JavaScript (フロントエンド)

#### 認証付きAPI呼び出し
```javascript
const apiCall = async (endpoint, options = {}) => {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch(`/api${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers
    }
  });
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  
  return response.json();
};
```

#### SSE接続
```javascript
const startSSEStream = async (conversationId, message, token) => {
  const response = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ 
      conversation_id: conversationId || "",  // 空文字で新規作成
      message 
    }),
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        
        // 新規会話作成イベント
        if (data.type === 'conversation_created') {
          const newConvId = data.conversation_id;
          if (!conversationId) {
            setConversationId(newConvId);
            navigate(`/chat/${newConvId}`);
          }
        }
        
        if (data.role === 'assistant') {
          // アシスタント応答の処理
          updateChatMessage(data.content);
        } else if (data.role === 'tool') {
          // ツール実行結果の処理  
          displayToolExecution(JSON.parse(data.content));
        }
      }
    }
  }
};
```

### Python (テスト/管理ツール)

```python
import requests

class ChatAPIClient:
    def __init__(self, base_url="http://localhost:8000", token=None):
        self.base_url = base_url
        self.token = token
        
    def login(self, email, password):
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"email": email, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        return data
        
    def get_conversations(self, skip=0, limit=20):
        response = requests.get(
            f"{self.base_url}/api/conversations",
            headers={"Authorization": f"Bearer {self.token}"},
            params={"skip": skip, "limit": limit}
        )
        response.raise_for_status()
        return response.json()
```

---

## バージョニング

**現在のバージョン**: `v1`
- API URLは `/api/` で始まります
- 将来的に `/api/v2/` のような明示的なバージョニングを検討

## 更新履歴

- **2025-08-23**: API設計書初版作成
- 認証システム、会話管理、SSEストリーミング仕様を定義
- ツール実行機能の詳細仕様を追加
- **2025-08-23 更新**: SSEエンドポイント仕様を大幅改善
  - エンドポイントURL固定化: `POST /api/chat/stream`
  - conversation_idをリクエストボディに移動（空文字で新規作成）
  - conversation_createdイベント追加でリアルタイム会話ID通知
  - API呼び出し回数削減（新規チャット時: 3回→1回）
  - フロントエンド実装の大幅簡素化