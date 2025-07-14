# WebSocketからSSEへの移行計画

## 背景

現在、WebSocketを使用してリアルタイムチャット機能を実装していますが、以下の理由によりServer-Sent Events (SSE)への移行を実施します：

### SSE移行の理由

1. **将来的なFunction Calling/MCP対応**
   - ツールの使用状況やステータスを段階的に表示する必要がある
   - 「〜〜〜ツールを使用しています。」「〜〜〜を調べています。」等の中間ステータス表示
   - 複数のイベントタイプを順次送信する場合、SSEのシンプルなイベントストリームが管理しやすい

2. **インフラストラクチャーの利点**
   - HTTP/HTTPSベースでプロキシ・ロードバランサーとの互換性が高い
   - Authorizationヘッダーによる認証が簡単
   - EventSourceの自動再接続機能
   - ファイアウォールでブロックされにくい

3. **チャットアプリケーションの特性**
   - 一方向通信（サーバー→クライアント）で十分
   - 双方向通信が不要

## 現在の実装状況

### バックエンド (backend/app/main.py)
- **WebSocketエンドポイント**: `/ws/{conversation_id}`
- **認証方式**: クエリパラメータでJWTトークン
- **ストリーミング**: OpenAI AsyncClientでリアルタイム送信
- **イベントタイプ**: `start`, `stream`, `end`

### フロントエンド (frontend/src/App.tsx)
- **WebSocketクライアント**: native WebSocket API
- **状態管理**: `streamingMessage` stateでリアルタイム表示
- **エラーハンドリング**: 手動での再接続ロジック

## 移行計画

### Phase 1: SSEエンドポイントの実装（バックエンド）

#### 1.1 新しいSSEエンドポイントの作成
```python
@app.get("/api/chat/stream/{conversation_id}")
async def stream_chat(
    conversation_id: str,
    message: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
```

#### 1.2 SSEレスポンス形式の定義
```python
# イベントタイプ
- status: ツール/処理のステータス更新
- content: チャットコンテンツのストリーム
- done: 処理完了
- error: エラー発生
```

#### 1.3 FastAPIでのSSE実装
```python
from fastapi.responses import StreamingResponse
import json

async def generate_sse_stream():
    yield f"data: {json.dumps({'type': 'status', 'message': 'AIが考えています...'})}\n\n"
    # OpenAI streaming
    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
    yield f"data: {json.dumps({'type': 'done'})}\n\n"
```

### Phase 2: フロントエンドのSSE実装

#### 2.1 EventSource APIの実装
```typescript
const handleSSEStream = (conversationId: string, message: string) => {
  const eventSource = new EventSource(
    `/api/chat/stream/${conversationId}?message=${encodeURIComponent(message)}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  
  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // handle different event types
  };
};
```

#### 2.2 状態管理の更新
```typescript
interface StreamingState {
  isStreaming: boolean;
  status: string | null;        // ツール使用状況
  content: string;              // チャットコンテンツ
  messageId: string | null;
}
```

### Phase 3: 段階的移行

#### 3.1 並行運用期間
- WebSocketとSSE両方のエンドポイントを維持
- フロントエンドで機能フラグによる切り替え
- テスト・デバッグ期間を設ける

#### 3.2 移行完了
- WebSocketエンドポイントの削除
- 関連するコードのクリーンアップ

## 実装詳細

### バックエンド変更点

#### 新規ファイル構成
```
backend/app/
├── main.py              # 既存（WebSocket削除予定）
├── routers/
│   └── chat_sse.py     # 新規SSEルーター
├── services/
│   └── streaming.py    # ストリーミング処理の共通化
└── models/
    └── streaming.py    # SSE用のPydanticモデル
```

#### SSE用のPydanticモデル
```python
class SSEEvent(BaseModel):
    type: Literal["status", "content", "done", "error"]
    message: Optional[str] = None
    content: Optional[str] = None
    tool_name: Optional[str] = None
    step: Optional[str] = None

class ChatSSERequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
```

### フロントエンド変更点

#### 新規コンポーネント/フック
```
frontend/src/
├── hooks/
│   └── useSSEStream.ts     # SSEストリーミング専用フック
├── components/
│   └── StatusIndicator.tsx # ツールステータス表示コンポーネント
└── types/
    └── streaming.ts        # SSE関連の型定義
```

#### useSSEStreamフックの実装例
```typescript
export const useSSEStream = () => {
  const [streamingState, setStreamingState] = useState<StreamingState>({
    isStreaming: false,
    status: null,
    content: '',
    messageId: null
  });

  const startStream = (conversationId: string, message: string) => {
    // EventSource implementation
  };

  return { streamingState, startStream };
};
```

## 将来のFunction Calling/MCP対応

### ステータス表示の拡張
```python
# ツール使用時のイベント例
yield f"data: {json.dumps({'type': 'status', 'message': 'Webページを検索しています...', 'tool_name': 'web_search'})}\n\n"
yield f"data: {json.dumps({'type': 'status', 'message': 'データベースを調べています...', 'tool_name': 'database_query'})}\n\n"
yield f"data: {json.dumps({'type': 'status', 'message': '計算を実行しています...', 'tool_name': 'calculator'})}\n\n"
yield f"data: {json.dumps({'type': 'content', 'content': '検索結果: ...'})}\n\n"
```

### UI表示イメージ
```
🔍 Webページを検索しています...
📊 データベースを調べています...
🧮 計算を実行しています...

AI: 検索結果によると、...
```

## スケジュール

| Phase | 作業内容 | 期間 |
|-------|----------|------|
| Phase 1 | SSEバックエンド実装 | 1-2日 |
| Phase 2 | SSEフロントエンド実装 | 1-2日 |
| Phase 3 | テスト・移行・クリーンアップ | 1日 |

## リスク・注意点

1. **ブラウザの同時接続制限**
   - SSEは同一ドメインあたり6接続まで
   - 複数タブでの同時使用時に注意

2. **認証ヘッダーのサポート**
   - EventSourceはヘッダー設定に制限がある
   - fetch APIでのSSE実装も検討

3. **エラーハンドリング**
   - ネットワーク切断時の自動再接続
   - 認証失効時の適切な処理

4. **後方互換性**
   - 既存のWebSocket実装の段階的削除
   - データベースマイグレーション不要（APIレベルの変更のみ）

## 結論

SSEへの移行により、よりシンプルで保守性の高いリアルタイム通信を実現し、将来のFunction Calling/MCP機能の実装基盤を構築します。段階的な移行により、既存機能への影響を最小限に抑えながら安全に移行を完了させます。