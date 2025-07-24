# Phase 1: バックエンドツール機能実装（データ保存対応版）

## 概要

第一段階では、バックエンドのAIエージェントにツール機能を追加し、将来のPhase 2を見越した軽量なデータ保存を行います。フロントエンドの変更は最小限に抑えつつ、ツール実行情報の基本的な記録を開始します。

## 実装方針の修正

### 基本原則（修正版）
- **最小限のフロントエンド変更**: 既存のSSEイベント構造はほぼ維持、軽微な拡張のみ
- **内部ツール実行**: ツール実行の詳細状況はフロントエンドに送信しない
- **最終レスポンス中心**: 完成されたテキストをストリーミング配信
- **軽量なデータ保存**: Phase 2への準備として基本的なツール情報を保存
- **後方互換性確保**: 既存の会話データとの完全な互換性を維持

### 実装対象
1. ツール関数の定義
2. エージェント設定の更新  
3. ストリーミング処理の修正
4. **軽量なデータベース拡張**（Phase 2への準備）
5. 最小限のフロントエンド調整
6. 既存APIとの互換性維持

## 重要な設計変更

### データベース設計（Phase 1）

#### Message テーブルの軽量拡張
```python
class Message(Base):
    # 既存フィールド...
    
    # Phase 1で追加（Phase 2への準備）
    tool_metadata = Column(JSON, nullable=True)  # ツール実行の概要情報
    
    # tool_metadata の構造例:
    # {
    #   "tools_used": [
    #     {
    #       "name": "calculate", 
    #       "input": {"expression": "2+3*4"},
    #       "output": "14",
    #       "execution_time_ms": 45,
    #       "status": "success"
    #     }
    #   ],
    #   "summary": {
    #     "total_tools": 1,
    #     "total_time_ms": 45,
    #     "success_count": 1,
    #     "error_count": 0
    #   }
    # }
```

#### マイグレーション（Phase 1）
```python
# alembic/versions/xxx_add_tool_metadata.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

def upgrade():
    op.add_column('messages', sa.Column('tool_metadata', JSON, nullable=True))
    op.create_index('idx_messages_tool_metadata', 'messages', ['tool_metadata'], 
                   postgresql_using='gin', postgresql_where=sa.text('tool_metadata IS NOT NULL'))

def downgrade():
    op.drop_index('idx_messages_tool_metadata', table_name='messages')
    op.drop_column('messages', 'tool_metadata')
```

### SSEイベントの軽微な拡張（Phase 1）
```python
class SSEEvent(BaseModel):
    type: Literal["status", "content", "done", "error"]
    message: str | None = None
    content: str | None = None
    message_id: str | None = None
    
    # Phase 1で追加（既存コードに影響なし）
    tool_summary: Optional[Dict[str, Any]] = None  # メッセージ完了時のツール概要
    
    # Phase 2で使用予定（Phase 1では null）
    tool_name: str | None = None  
    step: str | None = None
```

## 実装内容

### 1. ツール関数の実装

#### 1.1 基本ツールの定義
```python
# app/tools/__init__.py (新規作成)
from .basic_tools import get_current_time, calculate

__all__ = ["get_current_time", "calculate"]

# app/tools/basic_tools.py (新規作成)
from agents import function_tool
from datetime import UTC, datetime
import ast
import operator

@function_tool
def get_current_time() -> str:
    """現在の時刻を取得します。"""
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

@function_tool  
def calculate(expression: str) -> str:
    """数式を計算します。安全な数式のみサポートします。
    
    Args:
        expression: 計算する数式（例: "2 + 3 * 4"）
    
    Returns:
        計算結果
    """
    try:
        # 安全な文字のみチェック
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in expression):
            return "エラー: 許可されていない文字が含まれています"
        
        # 基本的な数式評価（本番では安全な評価器を使用）
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"計算エラー: {str(e)}"

# 利用可能なツールリスト
AVAILABLE_TOOLS = [get_current_time, calculate]
```

### 2. エージェント設定の更新

#### 2.1 main.pyの修正
```python
# app/main.py での変更点

# インポート追加
from .tools import get_current_time, calculate

# エージェント設定の更新
chat_agent = Agent(
    name="ChatAssistant",
    instructions="""あなたは親切で知識豊富なアシスタントです。
    ユーザーの質問に正確かつ丁寧に答えてください。
    必要に応じてツールを使用してください。
    時刻の取得や計算が必要な場合は、適切なツールを使用してください。
    回答は常にユーザーの言語で行ってください。""",
    model="gpt-4o",
    model_settings=ModelSettings(
        max_tokens=1024,
        temperature=0.7,
    ),
    tools=[get_current_time, calculate]  # ツールを追加
)
```

### 3. ストリーミング処理の修正（ツール情報保存対応）

#### 3.1 ツール実行情報の収集と保存
```python
# app/main.py の stream_chat 関数を修正

class ToolExecutionTracker:
    """Phase 1用の軽量ツール実行追跡"""
    def __init__(self):
        self.tools_used = []
        self.current_tool = None
        
    def start_tool(self, tool_name: str, arguments: dict):
        self.current_tool = {
            "name": tool_name,
            "input": arguments,
            "start_time": time.time() * 1000,
            "status": "executing"
        }
        
    def complete_tool(self, output: str, error: str = None):
        if self.current_tool:
            self.current_tool.update({
                "output": output,
                "error": error,
                "status": "success" if not error else "error",
                "execution_time_ms": int(time.time() * 1000 - self.current_tool["start_time"])
            })
            self.tools_used.append(self.current_tool)
            self.current_tool = None
            
    def get_metadata(self) -> dict:
        if not self.tools_used:
            return None
            
        return {
            "tools_used": self.tools_used,
            "summary": {
                "total_tools": len(self.tools_used),
                "total_time_ms": sum(t.get("execution_time_ms", 0) for t in self.tools_used),
                "success_count": len([t for t in self.tools_used if t["status"] == "success"]),
                "error_count": len([t for t in self.tools_used if t["status"] == "error"])
            }
        }

async def generate_sse_stream():
    try:
        # 既存の会話取得・ユーザーメッセージ保存処理
        
        # ツール実行追跡の初期化
        tool_tracker = ToolExecutionTracker()
        
        # API用メッセージ履歴を準備
        api_messages = [
            {"role": m.role, "content": m.content} for m in conv.messages
        ]

        # ストリーミング開始
        assistant_content = ""
        assistant_id = str(uuid.uuid4())
        result = Runner.run_streamed(chat_agent, api_messages)

        async for event in result.stream_events():
            if event.type == "raw_response_event":
                # ResponseTextDeltaEventの正確な処理
                if isinstance(event.data, ResponseTextDeltaEvent):
                    content = event.data.delta
                    if content:
                        assistant_content += content
                        
                        # フロントエンドにコンテンツストリーミング
                        content_event = SSEEvent(
                            type="content", 
                            content=content, 
                            message_id=assistant_id
                        )
                        yield f"data: {content_event.model_dump_json()}\n\n"
            
            elif event.type == "run_item_stream_event":
                if event.item.type == "tool_call_item":
                    # ツール実行開始（内部追跡）
                    tool_tracker.start_tool(
                        event.item.raw_item.name,
                        event.item.raw_item.arguments
                    )
                    print(f"[Phase1] Tool started: {event.item.raw_item.name}")
                    
                elif event.item.type == "tool_call_output_item":
                    # ツール実行完了（内部追跡）
                    tool_tracker.complete_tool(event.item.output)
                    print(f"[Phase1] Tool completed: {event.item.output}")

        # アシスタントメッセージ保存（ツールメタデータ含む）
        tool_metadata = tool_tracker.get_metadata()
        
        assistant_msg = Message(
            id=assistant_id,
            conversation_id=conv.id,
            role="assistant",
            content=assistant_content,
            tool_metadata=tool_metadata  # Phase 1で追加
        )
        db.add(assistant_msg)
        
        # ツール概要をフロントエンドに送信（オプション）
        if tool_metadata:
            summary_event = SSEEvent(
                type="done",
                message="Response completed",
                message_id=assistant_id,
                tool_summary=tool_metadata["summary"]  # Phase 1で追加
            )
            yield f"data: {summary_event.model_dump_json()}\n\n"
        else:
            # 通常の完了イベント
            done_event = SSEEvent(type="done", message_id=assistant_id)
            yield f"data: {done_event.model_dump_json()}\n\n"
        
        # 既存のタイトル生成・完了処理
        
    except Exception as e:
        # 既存のエラーハンドリング
```

### 4. フロントエンド対応（最小限の変更）

#### 4.1 TypeScript型定義の軽微な拡張
```typescript
// 既存のSSEイベント型を拡張
interface SSEEvent {
    type: 'status' | 'content' | 'done' | 'error';
    message?: string;
    content?: string;
    message_id?: string;
    
    // Phase 1で追加（オプション、既存コードに影響なし）
    tool_summary?: {
        total_tools: number;
        total_time_ms: number;
        success_count: number;
        error_count: number;
    };
}
```

#### 4.2 フロントエンド処理の軽微な調整
```typescript
// 既存のSSEイベント処理に小さな拡張を追加
const handleSSEEvent = (data: SSEEvent) => {
    switch (data.type) {
        case 'content':
            // 既存のコンテンツストリーミング処理（変更なし）
            appendToMessage(data.content);
            break;
            
        case 'done':
            // 完了処理に軽微な拡張
            setIsStreaming(false);
            
            // Phase 1で追加: ツール使用情報の軽微な表示（オプション）
            if (data.tool_summary && data.tool_summary.total_tools > 0) {
                console.log(`Tools used: ${data.tool_summary.total_tools} (${data.tool_summary.total_time_ms}ms)`);
                // 必要に応じて軽微なUI表示を追加
            }
            break;
            
        case 'error':
            // 既存のエラー処理（変更なし）
            handleError(data.message);
            break;
    }
};
```

#### 4.3 過去の会話での表示（Phase 1の準備）
```typescript
// 既存のメッセージ表示に軽微な拡張
interface Message {
    id: string;
    role: string;
    content: string;
    timestamp: string;
    
    // Phase 1で追加（オプション）
    tool_metadata?: {
        tools_used: Array<{
            name: string;
            status: string;
            execution_time_ms: number;
        }>;
        summary: {
            total_tools: number;
            total_time_ms: number;
        };
    };
}

// メッセージ表示コンポーネントの軽微な拡張
const MessageDisplay: React.FC<{message: Message}> = ({message}) => {
    return (
        <div className="message">
            <div className="content">{message.content}</div>
            
            {/* Phase 1で追加: 軽微なツール情報表示 */}
            {message.tool_metadata && (
                <div className="tool-info-subtle">
                    <small className="text-muted">
                        {message.tool_metadata.summary.total_tools}個のツールを使用 
                        ({message.tool_metadata.summary.total_time_ms}ms)
                    </small>
                </div>
            )}
        </div>
    );
};
```

#### 4.4 CSS（軽微な追加のみ）
```css
.tool-info-subtle {
    margin-top: 4px;
    font-size: 11px;
    color: #666;
    opacity: 0.7;
}
```

## 実装手順（修正版）

### Step 1: データベース拡張
1. `tool_metadata` カラム追加のマイグレーション作成
2. Alembic実行でテーブル更新
3. インデックス作成

### Step 2: ツールモジュール作成
1. `app/tools/` ディレクトリ作成
2. `app/tools/__init__.py` と `app/tools/basic_tools.py` ファイル作成
3. 基本ツール（時刻取得、計算）実装
4. 適切なモジュール構造での公開

### Step 3: バックエンド実装
1. `ToolExecutionTracker` クラス実装
2. `chat_agent` の設定にツールを追加
3. ストリーミング処理の修正（ツール情報保存対応）
4. SSEEventの軽微な拡張

### Step 4: フロントエンド軽微調整
1. TypeScript型定義の拡張
2. SSEイベント処理の軽微な調整
3. メッセージ表示の軽微な拡張
4. CSS追加

### Step 5: テスト・検証
1. 基本機能テスト: 時刻取得、計算
2. データ保存確認: `tool_metadata` の記録
3. 既存機能のリグレッションテスト
4. フロントエンド表示確認

## 期待される動作（修正版）

### ユーザー体験
1. **時刻取得**
   - 入力: 「今の時間は？」
   - 出力: 「現在の時刻は2025-01-23 15:30:00 UTCです。」
   - 表示: 「1個のツールを使用 (23ms)」（軽微な表示）

2. **計算機能**
   - 入力: 「2+3*4の計算をして」
   - 出力: 「2+3*4 = 14」
   - 表示: 「1個のツールを使用 (45ms)」（軽微な表示）

3. **過去の会話**
   - 既存の会話を開いた時も軽微なツール情報が表示される

### 内部動作
- ツール実行情報が `tool_metadata` に保存される
- サーバーログに実行情報が出力される
- フロントエンドには軽微なツール概要が表示される

### データベース保存例
```json
{
  "tools_used": [
    {
      "name": "calculate",
      "input": {"expression": "2+3*4"},
      "output": "14",
      "status": "success",
      "execution_time_ms": 45
    }
  ],
  "summary": {
    "total_tools": 1,
    "total_time_ms": 45,
    "success_count": 1,
    "error_count": 0
  }
}
```

## Phase 2への移行計画

### データ互換性の確保
1. **Phase 1のデータ活用**: `tool_metadata` をPhase 2で活用
2. **段階的テーブル追加**: 既存データを保持しつつ `ToolExecution` テーブル追加
3. **後方互換性**: Phase 1のデータもPhase 2で表示可能

### 移行戦略
```python
# Phase 2での移行処理例
def migrate_phase1_to_phase2(message: Message):
    """Phase 1のtool_metadataからToolExecutionレコードを作成"""
    if message.tool_metadata:
        for i, tool_data in enumerate(message.tool_metadata["tools_used"]):
            execution = ToolExecution(
                message_id=message.id,
                execution_order=i + 1,
                tool_name=tool_data["name"],
                tool_arguments=tool_data["input"],
                execution_status="success" if tool_data["status"] == "success" else "error",
                tool_output=tool_data.get("output"),
                execution_time_ms=tool_data.get("execution_time_ms")
            )
            db.add(execution)
```

## リスク評価（修正版）

### 低リスク
- フロントエンド変更は最小限
- 既存API互換性維持
- データベース変更は軽微（カラム追加のみ）
- Phase 2への移行パスが明確

### 注意点
1. **データベースマイグレーション**: 本番環境での実行計画
2. **計算の安全性**: `eval()`の制限実装
3. **JSONカラムのサイズ**: 大量ツール実行時の考慮
4. **Phase 2移行時のデータ整合性確保**

## 成功の指標

### Phase 1完了時の確認項目
- [ ] ツール機能が正常動作
- [ ] `tool_metadata` が正しく保存される
- [ ] 既存機能に影響なし
- [ ] 軽微なフロントエンド表示が動作
- [ ] 過去の会話でツール情報が表示される
- [ ] Phase 2への移行準備が整っている

Phase 1により、安全にツール機能を導入し、Phase 2での詳細な可視化への確実な基盤を構築します。