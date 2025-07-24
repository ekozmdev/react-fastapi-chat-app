# Tool Use機能追加仕様書

## 概要
バックエンドのAIエージェントにtool_use機能を追加し、外部ツールの実行とリアルタイム状況表示を可能にする。

## 現在の実装状況

### AIエージェント
- openai-agents-python SDKを使用
- `Agent` + `Runner.run_streamed()` でストリーミング応答
- SSE (Server-Sent Events) でリアルタイム通信
- モデル: gpt-4o

### SSEイベント構造
```python
class SSEEvent(BaseModel):
    type: Literal["status", "content", "done", "error", "tool_start", "tool_end"]
    message: str | None = None
    content: str | None = None
    message_id: str | None = None
    tool_name: str | None = None
    tool_id: str | None = None
    tool_output: str | None = None
    step: str | None = None
```

## 変更内容

### 1. ツール定義の追加

#### 1.1 基本ツール実装（@function_toolデコレータ使用）
openai-agents-python SDK v0.2.3の`@function_tool`デコレータを使用してツールを実装する：

```python
from agents import function_tool
from pydantic import BaseModel

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
        # 安全な計算のため、許可された文字のみチェック
        allowed_chars = set('0123456789+-*/.() ')
        if all(c in allowed_chars for c in expression):
            result = eval(expression)  # 本番では数式評価ライブラリを使用
            return str(result)
        else:
            return "エラー: 許可されていない文字が含まれています"
    except Exception as e:
        return f"エラー: {str(e)}"

class SearchQuery(BaseModel):
    query: str
    max_results: int = 5

@function_tool
def web_search(search_query: SearchQuery) -> str:
    """Web検索を実行します。
    
    Args:
        search_query: 検索クエリと最大結果数
        
    Returns:
        検索結果
    """
    # TODO: 実際の検索API実装（DuckDuckGo API等）
    return f"検索結果: {search_query.query}に関する{search_query.max_results}件の情報"
```

#### 1.2 ツールリストの定義
```python
# 利用可能なツールのリスト
AVAILABLE_TOOLS = [get_current_time, calculate, web_search]
```

### 2. Agentの設定変更

```python
# Tools対応Agent設定
chat_agent = Agent(
    name="ChatAssistant",
    instructions="""あなたは親切で知識豊富なアシスタントです。
    ユーザーの質問に正確かつ丁寧に答えてください。
    必要に応じてツールを使用してください。
    回答は常にユーザーの言語で行ってください。""",
    model="gpt-4o",
    model_settings=ModelSettings(
        max_tokens=1024,
        temperature=0.7,
    ),
    tools=AVAILABLE_TOOLS  # @function_toolで定義されたツールリスト
)
```

### 3. ストリーミング処理の拡張

#### 3.1 正確なイベント処理（SDK v0.2.3準拠）
```python
from openai.types.responses import ResponseTextDeltaEvent

async for event in result.stream_events():
    if event.type == "raw_response_event":
        # 正確な型チェックでテキストストリーミング
        if isinstance(event.data, ResponseTextDeltaEvent):
            content = event.data.delta
            if content:
                assistant_content += content
                # コンテンツストリーミング
                content_event = SSEEvent(
                    type="content", 
                    content=content, 
                    message_id=assistant_id
                )
                yield f"data: {content_event.model_dump_json()}\n\n"
    
    elif event.type == "run_item_stream_event":
        if event.item.type == "tool_call_item":
            # ツール呼び出し開始
            tool_name = event.item.raw_item.name
            tool_id = event.item.id
            
            tool_start_event = SSEEvent(
                type="tool_start",
                message=f"ツール実行中: {tool_name}",
                tool_name=tool_name,
                tool_id=tool_id
            )
            yield f"data: {tool_start_event.model_dump_json()}\n\n"
            
        elif event.item.type == "tool_call_output_item":
            # ツール実行完了
            tool_output = event.item.output
            
            tool_end_event = SSEEvent(
                type="tool_end",
                message="ツール実行完了",
                tool_output=tool_output,
                tool_id=event.item.tool_call_id
            )
            yield f"data: {tool_end_event.model_dump_json()}\n\n"
    
    elif event.type == "agent_updated_stream_event":
        # エージェント状態の更新（オプション）
        status_event = SSEEvent(
            type="status",
            message=f"エージェント状態更新: {event.agent.name}"
        )
        yield f"data: {status_event.model_dump_json()}\n\n"
```

### 4. フロントエンド対応

#### 4.1 ツール実行状況の表示フロー

**基本的な表示フロー：**
1. ユーザーがメッセージ送信
2. ツール実行が必要な場合：「○○○を実行中...」表示
3. ツール実行完了後：最終的なテキストをストリーミング表示

#### 4.2 状態管理の拡張
```typescript
interface ToolExecutionState {
    isExecuting: boolean;
    currentTool: string | null;
    executionMessage: string | null;
    executedTools: {
        name: string;
        output: string;
        timestamp: number;
    }[];
}

interface MessageState {
    content: string;
    isStreaming: boolean;
    toolExecution: ToolExecutionState;
}

const [messageState, setMessageState] = useState<MessageState>({
    content: '',
    isStreaming: false,
    toolExecution: {
        isExecuting: false,
        currentTool: null,
        executionMessage: null,
        executedTools: []
    }
});
```

#### 4.3 SSEイベント処理の詳細実装
```typescript
const handleSSEEvent = (data: SSEEvent) => {
    switch (data.type) {
        case 'tool_start':
            setMessageState(prev => ({
                ...prev,
                toolExecution: {
                    ...prev.toolExecution,
                    isExecuting: true,
                    currentTool: data.tool_name,
                    executionMessage: getToolExecutionMessage(data.tool_name)
                }
            }));
            break;
        
        case 'tool_end':
            setMessageState(prev => ({
                ...prev,
                toolExecution: {
                    ...prev.toolExecution,
                    isExecuting: false,
                    currentTool: null,
                    executionMessage: null,
                    executedTools: [
                        ...prev.toolExecution.executedTools,
                        {
                            name: data.tool_name || 'unknown',
                            output: data.tool_output || '',
                            timestamp: Date.now()
                        }
                    ]
                }
            }));
            break;
        
        case 'content':
            // ツール実行完了後のテキストストリーミング
            setMessageState(prev => ({
                ...prev,
                content: prev.content + data.content,
                isStreaming: true
            }));
            break;
        
        case 'done':
            setMessageState(prev => ({
                ...prev,
                isStreaming: false
            }));
            break;
    }
};

// ツール実行メッセージの生成
const getToolExecutionMessage = (toolName: string): string => {
    const messages = {
        'get_current_time': '現在時刻を取得中...',
        'calculate': '計算を実行中...',
        'web_search': 'Web検索を実行中...'
    };
    return messages[toolName] || `${toolName}を実行中...`;
};
```

#### 4.4 UI コンポーネントの実装
```typescript
const ToolExecutionIndicator: React.FC<{ 
    execution: ToolExecutionState 
}> = ({ execution }) => {
    if (!execution.isExecuting) return null;
    
    return (
        <div className="tool-execution-indicator">
            <div className="loading-spinner" />
            <span className="execution-message">
                {execution.executionMessage}
            </span>
        </div>
    );
};

const MessageContent: React.FC<{ 
    messageState: MessageState 
}> = ({ messageState }) => {
    return (
        <div className="message-content">
            {/* ツール実行中の表示 */}
            <ToolExecutionIndicator execution={messageState.toolExecution} />
            
            {/* 実行済みツールの表示（オプション） */}
            {messageState.toolExecution.executedTools.map((tool, index) => (
                <div key={index} className="executed-tool">
                    <span className="tool-name">{tool.name}</span>
                    <span className="tool-output">{tool.output}</span>
                </div>
            ))}
            
            {/* メインコンテンツのストリーミング表示 */}
            <div className="streaming-content">
                {messageState.content}
                {messageState.isStreaming && <span className="cursor">|</span>}
            </div>
        </div>
    );
};
```

#### 4.5 CSS スタイリング例
```css
.tool-execution-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background-color: #f0f8ff;
    border-radius: 6px;
    margin-bottom: 8px;
    border-left: 3px solid #007bff;
}

.loading-spinner {
    width: 16px;
    height: 16px;
    border: 2px solid #e3e3e3;
    border-top: 2px solid #007bff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.execution-message {
    color: #007bff;
    font-size: 14px;
    font-style: italic;
}

.executed-tool {
    background-color: #f8f9fa;
    padding: 4px 8px;
    border-radius: 4px;
    margin: 4px 0;
    font-size: 12px;
    color: #6c757d;
}

.streaming-content {
    line-height: 1.6;
}

.cursor {
    animation: blink 1s infinite;
}

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
}
```

#### 4.6 ユーザーエクスペリエンスの考慮事項

1. **実行時間の表示**
   - 長時間実行されるツールの場合、経過時間を表示
   - タイムアウトの警告表示

2. **複数ツールの同時実行**
   - 複数のツールが順次実行される場合の表示方法
   - 進捗インジケーターの実装

3. **エラーハンドリング**
   - ツール実行失敗時の表示
   - リトライ機能の提供

4. **アクセシビリティ**
   - スクリーンリーダー対応
   - キーボードナビゲーション対応

### 5. セキュリティ考慮事項

#### 5.1 ツール実行の制限
- `calculate`ツールでの安全な数式評価（evalの代替）
- Web検索でのAPIキー管理とレート制限
- ツール実行タイムアウト設定（デフォルト30秒）
- 許可された文字のみでの入力検証

#### 5.2 権限管理
- ユーザー毎のツール使用権限設定
- ツール実行ログの記録とモニタリング
- 敏感な操作の認証確認

#### 5.3 実装での安全性対策
```python
# 安全な数式評価の例
import ast
import operator

def safe_eval(expression: str) -> float:
    """安全な数式評価（evalの代替）"""
    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.USub: operator.neg,
    }
    # AST解析による安全な評価
    # 詳細実装は省略
```

### 6. 段階的実装計画（改訂版）

#### **Phase 1: 基盤構築とデータ保存**
- **目的**: ツール機能の安全な導入と将来への準備
- **データベース変更**: `Message.tool_metadata` カラム追加
- **フロントエンド変更**: 最小限（軽微な表示追加）
- **主要機能**:
  - 基本ツール実装（時刻取得、計算）
  - ツール実行情報の JSON 保存
  - 軽微なツール概要表示

#### **Phase 2: 詳細可視化と完全追跡**
- **目的**: リアルタイム表示と詳細履歴機能
- **データベース変更**: `ToolExecution` テーブル追加、Phase 1データ移行
- **フロントエンド変更**: 段階的UI拡張（Phase 1互換性維持）
- **主要機能**:
  - 「📞→⏳→✅」段階表示
  - 詳細なツール実行履歴
  - Phase 1データの完全活用

#### **重要な設計原則**
1. **データ互換性**: Phase 1 → Phase 2 での完全なデータ保持
2. **段階的変更**: 大幅な変更を避け、既存機能への影響最小化
3. **後方互換性**: 各段階で既存機能の維持を保証
4. **リスク管理**: データベースマイグレーションの安全性確保

### 7. データベース変更の詳細

#### Phase 1: 軽量拡張
```sql
-- Message テーブルに JSON カラム追加
ALTER TABLE messages ADD COLUMN tool_metadata JSON;
CREATE INDEX idx_messages_tool_metadata ON messages USING GIN (tool_metadata) WHERE tool_metadata IS NOT NULL;
```

#### Phase 2: 詳細テーブル追加
```sql
-- ToolExecution テーブル作成
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
    execution_time_ms INTEGER
);

-- Message テーブルに詳細追跡フラグ追加
ALTER TABLE messages ADD COLUMN has_detailed_executions BOOLEAN DEFAULT FALSE;
```

### 8. テスト計画（段階別）

#### Phase 1 テスト
- [ ] ツール関数の単体テスト
- [ ] `tool_metadata` 保存の確認
- [ ] 既存機能のリグレッションテスト
- [ ] 軽微なフロントエンド表示の確認

#### Phase 2 テスト
- [ ] データ移行処理の検証
- [ ] リアルタイム表示のテスト
- [ ] 詳細履歴表示のテスト
- [ ] Phase 1データとの統合表示テスト
- [ ] パフォーマンス影響の測定

### 9. リスク管理と対策

#### データ関連リスク
- **マイグレーション失敗**: 事前バックアップとロールバック計画
- **データサイズ増加**: JSONカラムのサイズ監視とパージ戦略
- **互換性問題**: 各段階での互換性テスト実施

#### 運用リスク
- **パフォーマンス低下**: 段階的デプロイと監視強化
- **ツール実行エラー**: 詳細なエラーログとアラート
- **フロントエンド表示問題**: 段階的UI更新とフォールバック

### 10. 今後の拡張可能性

#### 短期的拡張（6ヶ月以内）
- ツール実行結果のキャッシュ機能
- Web検索ツールの本格実装
- エラー時の自動リトライ機能

#### 中期的拡張（1年以内）
- MCP (Model Context Protocol) 対応
- カスタムツールの動的追加
- ユーザー毎のツール権限管理

#### 長期的展望（1年以上）
- マルチエージェント対応
- ツール実行の並列化
- 高度な分析・監視ダッシュボード

この段階的アプローチにより、安全かつ確実にツール機能を拡張し、将来の要求にも柔軟に対応できる基盤を構築します。