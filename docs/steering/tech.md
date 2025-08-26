# 技術仕様（Tech Stack）

## 採用技術スタック

### フロントエンド

**フレームワーク・ライブラリ**
- **React**: 18.2.0+ (関数コンポーネント + Hooks)
- **TypeScript**: 5.2.2+ (Strict Mode)
- **React Router**: v7.6.3 (Outlet パターン)
- **react-markdown**: 10.1.0+ (Markdown レンダリング)
- **remark-gfm**: 4.0.1+ (GitHub Flavored Markdown)

**開発ツール**
- **Vite**: 7.0.5+ (ビルドツール)
- **Biome**: 2.1.2+ (リンター・フォーマッター)
- **Node.js**: 22+ (実行環境)

**対応ブラウザ**
- Chrome 100+, Firefox 100+, Safari 15+, Edge 100+
- Server-Sent Events サポート必須
- JavaScript 有効環境のみ

### バックエンド

**フレームワーク・ライブラリ**
- **FastAPI**: 最新安定版 (非同期Webフレームワーク)
- **Python**: 3.13+ (型ヒント必須)
- **SQLAlchemy**: 2.0+ (非同期ORM)
- **Alembic**: 最新版 (マイグレーション管理)
- **Pydantic**: 最新版 (データ検証)

**AI・外部API**
- **openai-agents-python**: 最新版 (OpenAI Agent SDK)
- **OpenAI API**: GPT-4o-mini (デフォルトモデル)

**開発ツール**
- **uv**: パッケージ管理
- **Ruff**: リンター・フォーマッター
- **pytest**: テスティングフレームワーク

### データベース

**RDBMS**
- **PostgreSQL**: 16+ (メインデータベース)
- **psycopg**: 3+ (データベースドライバー)

**接続仕様**
- 接続プール使用
- 非同期接続対応
- ACID特性準拠

### インフラ・運用

**コンテナ化**
- **Docker**: 最新安定版
- **Docker Compose**: v2+
- **Nginx**: Alpine版 (リバースプロキシ)

**環境管理**
- **.env**: 環境変数管理
- **dotenv**: 環境変数ローダー

## 技術規約

### Python (バックエンド)

**コーディング規約**
```python
# 型ヒント必須
def process_message(message: str, user_id: str) -> dict[str, Any]:
    pass

# 非同期処理パターン
async def handle_sse_stream(request: Request) -> StreamingResponse:
    async def generate():
        async for event in agent.run_streamed(messages):
            yield format_sse_event(event)
    return StreamingResponse(generate(), media_type="text/event-stream")

# エラーハンドリング
@app.exception_handler(CustomException)
async def custom_exception_handler(request: Request, exc: CustomException):
    return JSONResponse(status_code=400, content={"error": str(exc)})
```

**コード品質**
- 行長制限: 88文字 (Ruff準拠)
- インデント: 4スペース
- 関数・クラス名: snake_case / PascalCase
- 型ヒント: 必須 (dict[str, Any] 形式推奨)
- Docstring: 公開API用関数は必須

**推奨パターン**
- Pydantic モデルによるデータ検証
- FastAPI 依存注入システム活用
- SQLAlchemy 2.0 非同期パターン
- レイヤードアーキテクチャ (core/db/models/schemas分離)

### TypeScript/React (フロントエンド)

**コーディング規約**
```typescript
// 型定義必須
interface ToolExecutionState {
  callId: string;
  toolName: string;
  status: 'called' | 'executing' | 'completed' | 'failed';
  result?: any;
}

// 関数コンポーネント + Hooks
const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  
  const handleToolExecution = useCallback((result: ToolResult) => {
    setMessages(prev => [...prev, result]);
  }, []);
  
  return <div>...</div>;
};

// イベントハンドリング
const processSSEEvent = (data: SSEEventData) => {
  switch (data.role) {
    case 'tool':
      handleToolResult(data);
      break;
    case 'assistant':
      handleAssistantMessage(data);
      break;
  }
};
```

**コード品質**
- TypeScript Strict Mode
- 明示的な型定義 (any 型使用禁止)
- React Hooks ルール準拠
- Biome設定に基づくフォーマッティング
- ESNext対応 (import/export構文)

**推奨パターン**
- Context API による状態管理 (Redux不使用)
- useCallback/useMemo によるパフォーマンス最適化
- カスタムフックによるロジック分離
- React Router v6 Outlet パターン

### データベース設計規約

**テーブル設計**
```sql
-- 主キー: UUID-like String値
CREATE TABLE users (
    id VARCHAR PRIMARY KEY DEFAULT generate_unique_id(),
    email VARCHAR UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 外部キー制約必須
CREATE TABLE conversations (
    id VARCHAR PRIMARY KEY DEFAULT generate_unique_id(),
    user_id VARCHAR NOT NULL REFERENCES users(id),
    title VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- インデックス命名規則
CREATE INDEX idx_messages_conversation_created 
ON messages(conversation_id, created_at);
```

**データ形式規約**
- 日時: UTC タイムゾーン必須
- ID: UUID-like String値 (generate_unique_id()使用)
- JSON: ensure_ascii=False (日本語対応)
- 外部キー: 必ず制約設定

### API設計規約

**エンドポイント命名**
```
/api/auth/login          # 認証
/api/conversations       # リソースの複数形
/api/conversations/{id}  # 個別リソース
/api/chat/stream         # アクション (動詞)
```

**レスポンス形式**
```json
{
  "success": true,
  "data": {...},
  "timestamp": "2025-01-15T10:30:00Z"
}

// エラー時
{
  "success": false,
  "error": "エラーメッセージ",
  "detail": "詳細情報"
}
```

**SSE形式**
```
Content-Type: text/event-stream

data: {"role": "tool", "content": "...", "id": "..."}

data: {"role": "assistant", "content": "...", "id": "..."}

event: done
data: {"id": "assistant_123"}
```

## 技術制約・ガイドライン

### パフォーマンス

**フロントエンド**
- 初期ロード時間: 3秒以内
- ストリーミング応答: 100ms以内
- メモリ使用量: 100MB以内
- バンドルサイズ: 1MB以内

**バックエンド**
- API応答時間: 500ms以内
- SSEストリーミング開始: 1秒以内
- データベースクエリ: 200ms以内
- 同時接続: 100接続以上

### セキュリティ

**認証・認可**
```python
# JWT設定
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 1440  # 24時間

# パスワードハッシュ化
pwd_context = CryptContext(schemes=["bcrypt"])

# CORS設定
CORS_ALLOW_ORIGINS = ["http://localhost:3000"]
CORS_ALLOW_CREDENTIALS = True
```

**入力検証**
```python
class ChatRequest(BaseModel):
    conversation_id: str = Field("", max_length=100)
    message: str = Field(..., min_length=1, max_length=10000)
```

### 開発・運用

**ログレベル**
- DEBUG: 開発環境のみ
- INFO: 重要な処理開始・完了
- WARNING: 復旧可能なエラー
- ERROR: システムエラー

**環境変数**
```bash
# 必須
OPENAI_API_KEY=sk-xxxxx
JWT_SECRET_KEY=512bit-secure-key
DATABASE_URL=postgresql+psycopg://...

# オプション (デフォルト値あり)
OPENAI_MODEL=gpt-4o-mini
CORS_ORIGINS=http://localhost:3000
```

**テスト方針**
- ユニットテスト: pytest (バックエンド)
- 統合テスト: curl によるAPI検証
- E2Eテスト: 将来的にPlaywright検討

この技術仕様に基づき、一貫性のある実装と高い保守性を実現します。