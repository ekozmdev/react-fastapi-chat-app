# Phase 2: ツール実行状況の詳細可視化（Phase 1基盤活用版）

## 概要

Phase 1で構築したツール機能とデータ保存基盤を活用し、ツール実行状況の詳細なリアルタイム表示と完全な履歴追跡機能を実装します。Phase 1の `tool_metadata` データを保持しつつ、より詳細な `ToolExecution` テーブルを追加してエージェントのツール呼び出しから実際の実行完了まで全工程を可視化します。

## Phase 1からの改善課題

### 1. **詳細なリアルタイム表示**
- Phase 1: 軽微なツール概要表示のみ
- Phase 2: 「📞呼び出し中」→「⏳実行中」→「✅完了」の段階表示

### 2. **ツールコールと実行の詳細追跡**
- Phase 1: 成功/失敗の基本情報のみ
- Phase 2: エージェントの「呼び出し決定」→「実行開始」→「完了」の全工程

### 3. **豊富な履歴情報**
- Phase 1: 基本的なツール概要（個数、時間）
- Phase 2: 各ツールの入力、出力、エラー詳細、実行順序

### 4. **Phase 1データの活用**
- 既存の `tool_metadata` を保持・活用
- 段階的なデータ拡張により完全な下位互換性を確保

## Phase 1実装から得た重要な学び

### マイグレーション関連の教訓
1. **Alembicの--autogenerateの落とし穴**
   - モデル変更後にマイグレーション作成でも、空のupgrade()/downgrade()が生成される場合がある
   - **対策**: マイグレーションファイル作成後は必ず内容を確認し、手動調整を行う

2. **PostgreSQL JSONカラムのインデックス制約**
   - `postgresql.JSON`型に単純なGINインデックスを作成するとエラーが発生
   - **対策**: Phase 2のToolExecutionテーブルでは適切なインデックス戦略を採用

3. **マイグレーション確認手順**
   ```bash
   # Phase 2実装時の推奨手順
   uv run alembic revision --autogenerate -m "Add ToolExecution table"
   # ↓ 生成されたファイルの内容確認（重要！）
   # ↓ 必要に応じて手動調整
   uv run alembic upgrade head
   ```

### openai-agents SDKイベント処理の知見
1. **大量の予期しないイベント**
   - `Runner.run_streamed()`で多数の`Unexpected event`ログが発生
   - **対策**: ログレベルの調整とイベントフィルタリングの改善

2. **ツール実行イベントの正確な検出**
   ```python
   # Phase 1で成功したパターン
   if hasattr(event, 'item') and hasattr(event.item, 'type'):
       if event.item.type == "tool_call_item":
           # ツール呼び出し開始
       elif event.item.type == "tool_call_output_item":
           # ツール実行完了
   ```

3. **引数なしツールの特殊処理**
   - `get_current_time()`のような引数なしツールは`arguments='{}'`が送信される
   - Phase 2のUI設計では適切にフィルタリングが必要

### ツール実行追跡アーキテクチャの成功パターン
1. **ToolExecutionTrackerクラスの有効性**
   - Phase 1で実装したトラッカーパターンは有効
   - Phase 2では専用テーブルとの組み合わせで更なる拡張

2. **JSONメタデータ構造の適切性**
   ```python
   # Phase 1で成功した構造（Phase 2でも活用）
   {
       "tools_used": [...],
       "summary": {
           "total_tools": 1,
           "total_time_ms": 45,
           "success_count": 1,
           "error_count": 0
       }
   }
   ```

## データベース設計（Phase 1との互換性重視）

### Phase 1から継承するMessageテーブル
```python
class Message(Base):
    # 既存フィールド...
    
    # Phase 1で追加済み（保持）
    tool_metadata = Column(JSON, nullable=True)  # Phase 1の軽量データを保持
    
    # Phase 2で追加
    has_detailed_executions = Column(Boolean, default=False)  # 詳細追跡の有無
    
    # リレーション（Phase 2で追加）
    tool_executions = relationship(
        "ToolExecution", 
        back_populates="message",
        order_by="ToolExecution.execution_order",
        cascade="all, delete-orphan"
    )
```

### 新設ToolExecutionテーブル（Phase 2）
```python
class ToolExecution(Base):
    """ツール実行の完全な記録"""
    __tablename__ = "tool_executions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, ForeignKey("messages.id"), nullable=False)
    
    # 実行順序と識別
    execution_order = Column(Integer, nullable=False)  # メッセージ内での実行順序 (1, 2, 3...)
    tool_call_id = Column(String, nullable=False)      # OpenAI側のツールコールID
    
    # ツール情報
    tool_name = Column(String, nullable=False)         # ツール名 (get_current_time, calculate)
    tool_arguments = Column(JSON, nullable=True)        # 入力パラメータ
    
    # 2段階の状態管理
    call_status = Column(String, nullable=False)        # called, executing, completed, failed
    execution_status = Column(String, nullable=True)    # success, error, timeout, skipped
    
    # 結果データ
    tool_output = Column(Text, nullable=True)           # 成功時の出力
    error_message = Column(Text, nullable=True)         # エラー時のメッセージ
    
    # 完全なタイムライン
    called_at = Column(DateTime, nullable=False)        # ツール呼び出し決定時刻
    started_at = Column(DateTime, nullable=True)        # 実行開始時刻
    completed_at = Column(DateTime, nullable=True)      # 実行完了時刻
    execution_time_ms = Column(Integer, nullable=True)  # 実行時間(ミリ秒)
    
    # メタデータ
    agent_reasoning = Column(Text, nullable=True)       # なぜこのツールを呼び出したか
    
    # リレーション
    message = relationship("Message", back_populates="tool_executions")

### Phase 2マイグレーション戦略

#### データベースマイグレーション（Phase 2）
```sql
-- 2025_01_24_add_tool_executions.sql
-- 新しいToolExecutionテーブル作成
CREATE TABLE tool_executions (
    id VARCHAR PRIMARY KEY,
    message_id VARCHAR NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    execution_order INTEGER NOT NULL,
    tool_call_id VARCHAR NOT NULL,
    tool_name VARCHAR NOT NULL,
    tool_arguments JSON,
    call_status VARCHAR NOT NULL,
    execution_status VARCHAR,
    tool_output TEXT,
    error_message TEXT,
    called_at TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    execution_time_ms INTEGER,
    agent_reasoning TEXT
);

-- Messageテーブルに軽微な追加
ALTER TABLE messages ADD COLUMN has_detailed_executions BOOLEAN DEFAULT FALSE;

-- インデックス作成
CREATE INDEX idx_tool_executions_message_id ON tool_executions(message_id);
CREATE INDEX idx_tool_executions_order ON tool_executions(message_id, execution_order);
CREATE INDEX idx_tool_executions_tool_name ON tool_executions(tool_name);
```

#### Phase 1データの移行処理
```python
def migrate_phase1_tool_metadata():
    """Phase 1のtool_metadataから基本的なToolExecutionレコードを作成"""
    
    # Phase 1でツール使用があったメッセージを取得
    messages_with_tools = db.query(Message).filter(
        Message.tool_metadata.isnot(None)
    ).all()
    
    for message in messages_with_tools:
        if not message.tool_metadata:
            continue
            
        tools_used = message.tool_metadata.get("tools_used", [])
        
        for i, tool_data in enumerate(tools_used):
            # Phase 1データから可能な限り復元
            execution = ToolExecution(
                message_id=message.id,
                execution_order=i + 1,
                tool_call_id=f"phase1_{message.id}_{i}",  # 仮のID
                tool_name=tool_data["name"],
                tool_arguments=tool_data.get("input", {}),
                call_status="completed",  # Phase 1では完了済みのみ
                execution_status=tool_data.get("status", "success"),
                tool_output=tool_data.get("output"),
                error_message=tool_data.get("error"),
                called_at=message.created_at,  # 概算
                started_at=message.created_at,  # 概算
                completed_at=message.created_at,  # 概算
                execution_time_ms=tool_data.get("execution_time_ms"),
                agent_reasoning="Migrated from Phase 1 data"
            )
            db.add(execution)
        
        # 詳細追跡フラグを更新
        message.has_detailed_executions = True
    
    db.commit()
    print(f"Migrated {len(messages_with_tools)} messages from Phase 1")
```
```

## バックエンド実装（Phase 1拡張版）

### Phase 1からの拡張: ツール実行管理クラス
```python
class ToolExecutionManager:
    """ツール実行のライフサイクル管理"""
    
    def __init__(self, message_id: str, db: Session):
        self.message_id = message_id
        self.db = db
        self.execution_order = 0
    
    def record_tool_call(self, tool_call_id: str, tool_name: str, arguments: dict) -> ToolExecution:
        """ツール呼び出しの記録"""
        self.execution_order += 1
        
        execution = ToolExecution(
            message_id=self.message_id,
            execution_order=self.execution_order,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            tool_arguments=arguments,
            call_status="called",
            called_at=datetime.now(UTC)
        )
        
        self.db.add(execution)
        self.db.commit()
        return execution
    
    def start_execution(self, tool_call_id: str) -> bool:
        """ツール実行開始"""
        execution = self._get_execution(tool_call_id)
        if execution:
            execution.call_status = "executing"
            execution.started_at = datetime.now(UTC)
            self.db.commit()
            return True
        return False
    
    def complete_execution(self, tool_call_id: str, output: str = None, error: str = None) -> bool:
        """ツール実行完了"""
        execution = self._get_execution(tool_call_id)
        if execution:
            execution.call_status = "completed"
            execution.completed_at = datetime.now(UTC)
            
            if error:
                execution.execution_status = "error"
                execution.error_message = error
            else:
                execution.execution_status = "success"
                execution.tool_output = output
            
            if execution.started_at:
                execution.execution_time_ms = int(
                    (execution.completed_at - execution.started_at).total_seconds() * 1000
                )
            
            self.db.commit()
            return True
        return False
    
    def _get_execution(self, tool_call_id: str) -> ToolExecution:
        return self.db.query(ToolExecution).filter(
            ToolExecution.tool_call_id == tool_call_id,
            ToolExecution.message_id == self.message_id
        ).first()
    
    def finalize_message(self) -> dict:
        """メッセージ完了時の統計更新"""
        executions = self.db.query(ToolExecution).filter(
            ToolExecution.message_id == self.message_id
        ).all()
        
        # Messageテーブルの統計更新
        message = self.db.query(Message).filter(Message.id == self.message_id).first()
        if message:
            message.has_tool_executions = len(executions) > 0
            message.tool_execution_count = len(executions)
            self.db.commit()
        
        return {
            "total_called": len(executions),
            "total_executed": len([e for e in executions if e.execution_status == "success"]),
            "total_failed": len([e for e in executions if e.execution_status == "error"]),
            "tools_used": list(set(e.tool_name for e in executions)),
            "total_execution_time": sum(e.execution_time_ms or 0 for e in executions)
        }
```

### 拡張されたSSEイベント
```python
class SSEEvent(BaseModel):
    type: Literal[
        "status", "content", "done", "error", 
        "tool_call", "tool_start", "tool_end", "tool_error"
    ]
    message: str | None = None
    content: str | None = None
    message_id: str | None = None
    
    # 詳細なツール実行情報
    tool_execution: Optional[Dict[str, Any]] = None
    # 構造例:
    # {
    #   "id": "exec_123",
    #   "tool_call_id": "call_abc", 
    #   "tool_name": "calculate",
    #   "execution_order": 1,
    #   "call_status": "executing",
    #   "execution_status": "success",
    #   "arguments": {"expression": "2+3*4"},
    #   "output": "14",
    #   "error": null,
    #   "execution_time_ms": 45
    # }
```

### 修正されたストリーミング処理
```python
async def generate_sse_stream():
    try:
        # 既存の会話取得・ユーザーメッセージ保存処理
        
        # ツール実行管理の初期化
        execution_manager = ToolExecutionManager(conv.id, db)
        
        # ストリーミング開始
        assistant_content = ""
        assistant_id = str(uuid.uuid4())
        result = Runner.run_streamed(chat_agent, api_messages)

        async for event in result.stream_events():
            if event.type == "raw_response_event":
                # 既存のコンテンツストリーミング処理
                if isinstance(event.data, ResponseTextDeltaEvent):
                    content = event.data.delta
                    if content:
                        assistant_content += content
                        content_event = SSEEvent(
                            type="content", 
                            content=content, 
                            message_id=assistant_id
                        )
                        yield f"data: {content_event.model_dump_json()}\n\n"
            
            elif event.type == "run_item_stream_event":
                if event.item.type == "tool_call_item":
                    # ツール呼び出し記録
                    execution = execution_manager.record_tool_call(
                        event.item.id,
                        event.item.raw_item.name,
                        event.item.raw_item.arguments
                    )
                    
                    # ツール呼び出し通知
                    tool_call_event = SSEEvent(
                        type="tool_call",
                        message=f"ツール '{execution.tool_name}' を呼び出しました",
                        tool_execution={
                            "id": execution.id,
                            "tool_call_id": execution.tool_call_id,
                            "tool_name": execution.tool_name,
                            "execution_order": execution.execution_order,
                            "call_status": "called",
                            "arguments": execution.tool_arguments
                        }
                    )
                    yield f"data: {tool_call_event.model_dump_json()}\n\n"
                    
                    # 実行開始
                    execution_manager.start_execution(event.item.id)
                    tool_start_event = SSEEvent(
                        type="tool_start",
                        message=f"ツール '{execution.tool_name}' を実行中...",
                        tool_execution={
                            "id": execution.id,
                            "tool_call_id": execution.tool_call_id,
                            "call_status": "executing"
                        }
                    )
                    yield f"data: {tool_start_event.model_dump_json()}\n\n"
                    
                elif event.item.type == "tool_call_output_item":
                    # 実行完了
                    success = execution_manager.complete_execution(
                        event.item.tool_call_id,
                        output=event.item.output
                    )
                    
                    if success:
                        execution = execution_manager._get_execution(event.item.tool_call_id)
                        tool_end_event = SSEEvent(
                            type="tool_end",
                            message=f"ツール '{execution.tool_name}' 実行完了",
                            tool_execution={
                                "id": execution.id,
                                "tool_call_id": execution.tool_call_id,
                                "call_status": "completed",
                                "execution_status": "success",
                                "output": execution.tool_output,
                                "execution_time_ms": execution.execution_time_ms
                            }
                        )
                        yield f"data: {tool_end_event.model_dump_json()}\n\n"

        # アシスタントメッセージ保存
        db.add(Message(
            id=assistant_id,
            conversation_id=conv.id,
            role="assistant",
            content=assistant_content,
        ))

        # ツール実行統計の確定
        tool_summary = execution_manager.finalize_message()
        
        # 既存のタイトル生成・完了処理
        
    except Exception as e:
        # エラーハンドリング
```

## フロントエンド実装

### TypeScript型定義
```typescript
interface ToolExecution {
    id: string;
    toolCallId: string;
    toolName: string;
    executionOrder: number;
    callStatus: 'called' | 'executing' | 'completed' | 'failed';
    executionStatus?: 'success' | 'error' | 'timeout' | 'skipped';
    arguments?: any;
    output?: string;
    error?: string;
    calledAt: string;
    startedAt?: string;
    completedAt?: string;
    executionTimeMs?: number;
}

interface MessageWithTools {
    id: string;
    role: string;
    content: string;
    timestamp: string;
    hasToolExecutions: boolean;
    toolExecutionCount: number;
    toolExecutions: ToolExecution[];
}
```

### リアルタイム状態管理
```typescript
const [currentToolExecutions, setCurrentToolExecutions] = useState<Map<string, ToolExecution>>(new Map());

const handleSSEEvent = (data: SSEEvent) => {
    switch (data.type) {
        case 'tool_call':
            setCurrentToolExecutions(prev => new Map(prev).set(
                data.tool_execution.tool_call_id, 
                data.tool_execution as ToolExecution
            ));
            break;
        
        case 'tool_start':
            setCurrentToolExecutions(prev => {
                const updated = new Map(prev);
                const existing = updated.get(data.tool_execution.tool_call_id);
                if (existing) {
                    updated.set(data.tool_execution.tool_call_id, {
                        ...existing,
                        callStatus: 'executing',
                        startedAt: new Date().toISOString()
                    });
                }
                return updated;
            });
            break;
        
        case 'tool_end':
            setCurrentToolExecutions(prev => {
                const updated = new Map(prev);
                const existing = updated.get(data.tool_execution.tool_call_id);
                if (existing) {
                    updated.set(data.tool_execution.tool_call_id, {
                        ...existing,
                        callStatus: 'completed',
                        executionStatus: 'success',
                        output: data.tool_execution.output,
                        completedAt: new Date().toISOString(),
                        executionTimeMs: data.tool_execution.execution_time_ms
                    });
                }
                return updated;
            });
            break;
        
        case 'content':
            // 既存のコンテンツストリーミング処理
            break;
        
        case 'done':
            // ストリーミング完了時にツール実行状況をクリア
            setCurrentToolExecutions(new Map());
            break;
    }
};
```

### UIコンポーネント

#### リアルタイム実行表示
```typescript
const ToolExecutionIndicator: React.FC<{
    executions: Map<string, ToolExecution>;
}> = ({ executions }) => {
    const executionArray = Array.from(executions.values())
        .sort((a, b) => a.executionOrder - b.executionOrder);
    
    if (executionArray.length === 0) return null;
    
    return (
        <div className="tool-executions-live">
            {executionArray.map(execution => (
                <ToolExecutionCard 
                    key={execution.toolCallId} 
                    execution={execution}
                    isLive={true}
                />
            ))}
        </div>
    );
};
```

#### 履歴表示用コンポーネント
```typescript
const MessageWithToolHistory: React.FC<{
    message: MessageWithTools;
    isHistorical?: boolean;
}> = ({ message, isHistorical = false }) => {
    const [showToolDetails, setShowToolDetails] = useState(false);
    
    return (
        <div className="message">
            <div className="message-content">{message.content}</div>
            
            {message.hasToolExecutions && (
                <div className="tool-executions-summary">
                    <button 
                        className="tool-summary-toggle"
                        onClick={() => setShowToolDetails(!showToolDetails)}
                    >
                        {message.toolExecutionCount}個のツールを実行
                        {isHistorical && " (過去の実行)"}
                        <span className={`toggle-icon ${showToolDetails ? 'open' : ''}`}>▼</span>
                    </button>
                    
                    {showToolDetails && (
                        <div className="tool-executions-details">
                            {message.toolExecutions.map(execution => (
                                <ToolExecutionCard 
                                    key={execution.id} 
                                    execution={execution}
                                    isLive={false}
                                    showTimestamp={isHistorical}
                                />
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
```

#### 共通ツール実行カード
```typescript
const ToolExecutionCard: React.FC<{
    execution: ToolExecution;
    isLive: boolean;
    showTimestamp?: boolean;
}> = ({ execution, isLive, showTimestamp = false }) => {
    const getStatusIcon = () => {
        if (execution.executionStatus === 'success') return '✅';
        if (execution.executionStatus === 'error') return '❌';
        if (execution.callStatus === 'executing') return '⏳';
        if (execution.callStatus === 'called') return '📞';
        return '❓';
    };
    
    const getStatusText = () => {
        if (execution.callStatus === 'executing') return '実行中...';
        if (execution.executionStatus === 'success') return '完了';
        if (execution.executionStatus === 'error') return 'エラー';
        if (execution.callStatus === 'called') return '呼び出し中';
        return '不明';
    };
    
    return (
        <div className={`tool-execution-card ${execution.executionStatus} ${isLive ? 'live' : 'historical'}`}>
            <div className="tool-header">
                <span className="status-icon">{getStatusIcon()}</span>
                <span className="tool-name">{execution.toolName}</span>
                <span className="execution-order">#{execution.executionOrder}</span>
                <span className="tool-status">{getStatusText()}</span>
                {execution.executionTimeMs && (
                    <span className="execution-time">{execution.executionTimeMs}ms</span>
                )}
            </div>
            
            {execution.arguments && (
                <div className="tool-input">
                    <strong>入力:</strong> {JSON.stringify(execution.arguments, null, 2)}
                </div>
            )}
            
            {execution.output && (
                <div className="tool-output">
                    <strong>結果:</strong> {execution.output}
                </div>
            )}
            
            {execution.error && (
                <div className="tool-error">
                    <strong>エラー:</strong> {execution.error}
                </div>
            )}
            
            {showTimestamp && execution.completedAt && (
                <div className="execution-timestamp">
                    実行日時: {new Date(execution.completedAt).toLocaleString()}
                </div>
            )}
        </div>
    );
};
```

### CSS スタイリング
```css
.tool-executions-live {
    margin: 8px 0;
    padding: 8px;
    background-color: #f8f9ff;
    border-radius: 6px;
    border-left: 3px solid #007bff;
}

.tool-executions-summary {
    margin-top: 8px;
}

.tool-summary-toggle {
    background: none;
    border: none;
    color: #007bff;
    cursor: pointer;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.toggle-icon {
    transition: transform 0.2s;
}

.toggle-icon.open {
    transform: rotate(180deg);
}

.tool-execution-card {
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 8px;
    margin: 4px 0;
    background-color: #fafafa;
}

.tool-execution-card.live {
    border-left: 3px solid #007bff;
    background-color: #f0f8ff;
}

.tool-execution-card.success {
    border-left-color: #28a745;
}

.tool-execution-card.error {
    border-left-color: #dc3545;
}

.tool-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: bold;
    margin-bottom: 4px;
}

.tool-input, .tool-output, .tool-error {
    font-size: 12px;
    margin: 4px 0;
    padding: 4px;
    background-color: #f5f5f5;
    border-radius: 3px;
}

.tool-error {
    background-color: #fff5f5;
    color: #d32f2f;
}

.execution-timestamp {
    font-size: 11px;
    color: #666;
    margin-top: 4px;
}

.status-icon {
    font-size: 16px;
}

.execution-order {
    background-color: #e0e0e0;
    color: #666;
    padding: 2px 6px;
    border-radius: 10px;
    font-size: 10px;
}

.execution-time {
    background-color: #e8f5e8;
    color: #2e7d32;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 10px;
}
```

## API拡張

### 履歴取得API
```python
@app.get("/api/conversations/{conversation_id}")
async def get_conversation_with_tools(
    conversation_id: str,
    include_tool_details: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conv:
        raise HTTPException(404, "Conversation not found")
    
    messages_data = []
    for message in conv.messages:
        message_data = {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "timestamp": message.created_at,
            "has_tool_executions": message.has_tool_executions,
            "tool_execution_count": message.tool_execution_count
        }
        
        if include_tool_details and message.has_tool_executions:
            message_data["tool_executions"] = [
                {
                    "id": exec.id,
                    "tool_call_id": exec.tool_call_id,
                    "tool_name": exec.tool_name,
                    "execution_order": exec.execution_order,
                    "call_status": exec.call_status,
                    "execution_status": exec.execution_status,
                    "arguments": exec.tool_arguments,
                    "output": exec.tool_output,
                    "error": exec.error_message,
                    "called_at": exec.called_at,
                    "started_at": exec.started_at,
                    "completed_at": exec.completed_at,
                    "execution_time_ms": exec.execution_time_ms
                }
                for exec in message.tool_executions
            ]
        
        messages_data.append(message_data)
    
    return {
        "conversation": {
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
        },
        "messages": messages_data
    }
```

## 実装手順（Phase 1基盤活用版）

### Step 1: Phase 1データの保護とマイグレーション準備

#### 1.1 Phase 1環境のバックアップ作成
```bash
# データベースバックアップ
pg_dump postgresql://chatuser:chatpassword@localhost:5432/chatdb > phase1_backup.sql

# 既存tool_metadataの確認
uv run python -c "
from app.database import SessionLocal
from app.models import Message
db = SessionLocal()
tool_messages = db.query(Message).filter(Message.tool_metadata.isnot(None)).count()
print(f'Tool metadata records: {tool_messages}')
db.close()
"
```

#### 1.2 マイグレーション作成のベストプラクティス（Phase 1の教訓を活用）
```bash
# Step 1: モデル変更の完了確認
python -c "from app.models import Base; print([t.name for t in Base.metadata.tables.values()])"

# Step 2: マイグレーション作成
uv run alembic revision --autogenerate -m "Add ToolExecution table and detailed tracking"

# Step 3: 生成されたマイグレーションファイルの確認（重要！）
# - upgrade()とdowngrade()が適切に生成されているか
# - PostgreSQL固有の制約（JSONインデックスなど）に問題がないか
# - 外部キー制約が正しく設定されているか

# Step 4: テスト環境での事前確認
uv run alembic upgrade head --sql  # SQL出力で事前確認
```

#### 1.3 Phase 1の実装品質チェック
```bash
# ツール機能の動作確認
curl -X POST http://localhost:8000/api/chat/stream/{conversation_id} \
  -H "Authorization: Bearer {token}" \
  -d '{"message": "今の時刻は？"}'

# tool_metadata保存確認
uv run python -c "
from app.database import SessionLocal
from app.models import Message
import json
db = SessionLocal()
latest_msg = db.query(Message).filter(Message.tool_metadata.isnot(None)).order_by(Message.created_at.desc()).first()
if latest_msg:
    print('Latest tool_metadata:', json.dumps(latest_msg.tool_metadata, indent=2))
db.close()
"
```

### Step 2: データベース拡張（段階的）
1. `ToolExecution` テーブルの作成
2. `Message.has_detailed_executions` カラム追加
3. インデックス作成
4. Phase 1データの移行実行（`migrate_phase1_tool_metadata`）
5. データ整合性の検証

### Step 3: バックエンド実装（拡張版）

#### 3.1 ToolExecutionManager の改良実装（Phase 1の教訓を反映）
```python
# app/tool_execution_manager.py (Phase 1のToolExecutionTrackerを拡張)
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

# Phase 1で学んだ：適切なログ設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Unexpected eventログの制御

class ToolExecutionManager:
    """Phase 2: データベース連携型ツール実行管理"""
    
    def __init__(self, db: Session, message_id: str):
        self.db = db
        self.message_id = message_id
        self.tools_used = []  # Phase 1互換性のため保持
        self.current_tool = None
        
    def start_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """ツール実行開始（Phase 1の成功パターンを踏襲）"""
        try:
            # Phase 1で学んだ：安全なattribute取得
            safe_arguments = arguments if isinstance(arguments, dict) else {}
            
            # Phase 2: データベースに詳細記録
            tool_execution = ToolExecution(
                message_id=self.message_id,
                tool_name=tool_name,
                arguments=safe_arguments,
                status='started',
                started_at=datetime.now(UTC),
                execution_order=len(self.tools_used) + 1
            )
            self.db.add(tool_execution)
            self.db.commit()
            
            # Phase 1互換性の維持
            self.current_tool = {
                "name": tool_name,
                "input": safe_arguments,
                "start_time": time.time() * 1000,
                "status": "executing",
                "execution_id": tool_execution.id
            }
            
            return tool_execution.id
            
        except Exception as e:
            logger.error(f"Tool start failed: {e}")
            # Phase 1で学んだ：エラー時のフォールバック
            return None
```

#### 3.2 改善されたイベント処理（Phase 1の問題を解決）
```python
# main.py でのストリーミング処理（Phase 1の改善版）
async for event in result.stream_events():
    try:
        # Phase 1で学んだ：hasattr()による安全なチェック
        if hasattr(event, 'item') and hasattr(event.item, 'type'):
            if event.item.type == "tool_call_item":
                tool_name = getattr(event.item, 'name', 'unknown')
                arguments = getattr(event.item, 'arguments', {})
                
                # Phase 2: 詳細な状態管理
                execution_id = tool_manager.start_tool(tool_name, arguments)
                
                # Phase 2: フロントエンドにツール開始イベント送信
                tool_start_event = SSEEvent(
                    type="tool_start",
                    tool_name=tool_name,
                    execution_id=execution_id,
                    message_id=assistant_id
                )
                yield f"data: {tool_start_event.model_dump_json()}\n\n"
                
            elif event.item.type == "tool_call_output_item":
                output = getattr(event.item, 'output', '')
                error = getattr(event.item, 'error', None)
                tool_manager.complete_tool(output=output, error=error)
                
        elif event.type == "raw_response_event":
            # Phase 1で成功したパターンを保持
            if (hasattr(event, "data") and hasattr(event.data, "delta") 
                and event.data.delta is not None and isinstance(event.data.delta, str)):
                
                content = str(event.data.delta)
                # Phase 1で発見した問題：{}の表示制御
                if content.strip() not in ['{}', '']:  # 空引数の除外
                    assistant_content += content
                    
                    content_event = SSEEvent(
                        type="content", 
                        content=content, 
                        message_id=assistant_id
                    )
                    yield f"data: {content_event.model_dump_json()}\n\n"
            else:
                # Phase 1で学んだ：ログレベルの適切な制御
                logger.debug(f"Unexpected event: {type(event.data)}")
                
    except Exception as e:
        # Phase 1で不足していた：包括的エラーハンドリング
        logger.error(f"Event processing error: {e}")
        continue  # ストリーミングを継続
```

#### 3.3 SSEイベントの拡張（Phase 1基盤を保持）
```python
# Phase 1のSSEEventを拡張（互換性保持）
class SSEEvent(BaseModel):
    type: Literal["status", "content", "done", "error", "tool_start", "tool_progress", "tool_complete"]
    message: str | None = None
    content: str | None = None
    message_id: str | None = None
    
    # Phase 1から継承
    tool_name: str | None = None
    step: str | None = None
    
    # Phase 2で追加
    execution_id: str | None = None
    tool_status: str | None = None
    progress: int | None = None  # 0-100
    tool_output: str | None = None
```

### Step 4: フロントエンド実装（段階的）
1. TypeScript型定義の拡張（Phase 1基盤を保持）
2. リアルタイム状態管理の実装
3. UIコンポーネントの段階的追加
4. Phase 1データとPhase 2データの統合表示
5. 後方互換性の確保

### Step 5: 段階的デプロイとテスト
1. Phase 1機能のリグレッションテスト
2. Phase 2新機能のテスト
3. データ移行の検証
4. パフォーマンス影響の確認
5. 本番環境での段階的展開

## Phase 1実装の教訓まとめ（Phase 2で活用）

### 🔥 **確実に実行すべき検証項目**
1. **マイグレーションファイルの内容確認**
   ```bash
   # 必ず実行：生成されたマイグレーションの確認
   cat alembic/versions/最新のファイル.py
   # 空のupgrade()/downgrade()でないことを確認
   ```

2. **モデル変更の反映確認**
   ```python
   # Phase 2実装前に必ず実行
   from app.models import Base
   print("Tables:", [t.name for t in Base.metadata.tables.values()])
   print("ToolExecution columns:", [c.name for c in Base.metadata.tables['tool_executions'].columns])
   ```

3. **openai-agents SDKイベントの事前テスト**
   ```python
   # ツール実行時のイベントタイプ確認
   async for event in result.stream_events():
       print(f"Event type: {event.type}, Has item: {hasattr(event, 'item')}")
       if hasattr(event, 'item'):
           print(f"Item type: {getattr(event.item, 'type', 'N/A')}")
   ```

### ⚠️ **Phase 1で発生した問題と対策**
1. **{}表示問題**: 引数なしツールの空引数表示
   - **対策**: `content.strip() not in ['{}', '']` でフィルタリング

2. **大量の Unexpected event ログ**
   - **対策**: `logger.setLevel(logging.INFO)` + debug レベルでの出力

3. **PostgreSQL JSON インデックスエラー**
   - **対策**: GIN インデックス作成時の適切なオペレータークラス指定

### 🚀 **Phase 2で改善すべき品質ポイント**
1. **エラーハンドリングの強化**
   ```python
   # Phase 1で不足していた包括的なエラー処理
   try:
       # ツール実行処理
   except Exception as e:
       logger.error(f"Tool execution error: {e}")
       # フォールバック処理
   ```

2. **型安全性の向上**
   ```python
   # Phase 2では必須：適切な型ヒント
   def start_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
   ```

3. **ログ品質の改善**
   ```python
   # Phase 1の問題：print文使用
   print(f"Unexpected event: {event}")
   
   # Phase 2で改善：構造化ログ
   logger.info("tool_execution_started", extra={
       "tool_name": tool_name,
       "execution_id": execution_id,
       "message_id": message_id
   })
   ```

### 📊 **成功パターンの再利用**
1. **ToolExecutionTracker のクラス設計**: 単一責任で拡張しやすい
2. **AVAILABLE_TOOLS リスト**: 新ツール追加が容易
3. **tool_metadata の JSON 構造**: Phase 2 でも活用可能
4. **hasattr() による安全なイベント処理**: 堅牢性が高い

**Phase 1 → Phase 2 移行の成功の鍵**: 上記の教訓を活かし、確実で品質の高い実装を行う

## 期待される動作

### リアルタイム体験
1. ユーザー: 「今の時間と2+3*4を教えて」
2. システム表示:
   ```
   📞 get_current_time を呼び出しました (#1)
   ⏳ get_current_time を実行中...
   ✅ get_current_time 完了 (23ms)
   📞 calculate を呼び出しました (#2)  
   ⏳ calculate を実行中...
   ✅ calculate 完了 (45ms)
   ```
3. 最終レスポンス: 「現在の時刻は2025-01-23 15:30:00 UTCです。また、2+3*4の計算結果は14です。」

### 履歴表示体験
- 過去の会話を開いた時
- 「2個のツールを実行 (過去の実行) ▼」をクリック
- 各ツールの詳細（入力、出力、実行時間、実行日時）が表示

## 運用・分析の可能性

### ユーザー向け機能
- ツール実行履歴の確認
- 実行時間の把握
- エラー発生時の詳細確認

### 開発・運用向け機能
- ツール使用頻度の分析
- 平均実行時間の監視
- エラー率の追跡
- パフォーマンスボトルネックの特定

### 将来的な拡張
- ツール実行結果のキャッシュ機能
- ユーザー別使用統計
- A/Bテストでのツール効果測定
- 自動リトライ機能

Phase 2の実装により、ユーザーはツール実行の全工程を可視化でき、過去の会話でも完全な実行履歴を確認できるようになります。