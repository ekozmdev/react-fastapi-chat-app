# OpenAI Agent SDK ストリーミングデータフロー

本文書では、OpenAI Agents Python SDKからの生のストリーミングレスポンスを受信し、バックエンドで処理してフロントエンドに送信、フロントエンドでレンダリングする一連のデータフローを詳細に説明します。

## アーキテクチャ概要

```
OpenAI Agents SDK → Backend (FastAPI) → Frontend (React)
      ↓                    ↓                   ↓
各種StreamEvent      SSE変換・集約        EventSource受信
生データ処理        データベース保存     リアルタイム表示
```

## 1. Agent SDK 生ストリーミングデータ（主要イベントシーケンス）

### 1.1 エージェント初期化フェーズ

```python
# エージェント更新通知
Stream Event: AgentUpdatedStreamEvent(
    new_agent=Agent(
        name='ChatAssistant',
        tools=[
            FunctionTool(name='get_current_time', ...),
            FunctionTool(name='calculate', ...),
            FunctionTool(name='web_search', ...)
        ],
        ...
    )
)
```

### 1.2 ツール決定・実行フェーズ

#### レスポンス作成開始
```python
Stream Event: RawResponsesStreamEvent(
    data=ResponseCreatedEvent(
        response=Response(
            id='resp_68ae8db80bac8190a1defb37d2c4c9a206980b07b64d526f',
            status='in_progress',
            tools=[...],  # 利用可能ツール一覧
            ...
        )
    )
)
```

#### レスポンス処理進行中
```python
Stream Event: RawResponsesStreamEvent(
    data=ResponseInProgressEvent(
        response=Response(
            id='resp_68ae8db80bac8190a1defb37d2c4c9a206980b07b64d526f',
            status='in_progress',
            ...
        )
    )
)
```

#### ツール呼び出し決定
```python
Stream Event: RawResponsesStreamEvent(
    data=ResponseOutputItemAddedEvent(
        item=ResponseFunctionToolCall(
            arguments='',
            call_id='call_WXXHRYxeBCIU72zUSGREMN22',
            name='get_current_time',
            type='function_call',
            status='in_progress'
        )
    )
)
```

#### ツール引数生成（増分）
```python
Stream Event: RawResponsesStreamEvent(
    data=ResponseFunctionCallArgumentsDeltaEvent(
        delta='{}',  # 引数の増分
        item_id='fc_68ae8db8b18c819097496bb68c17d3bd06980b07b64d526f'
    )
)
```

#### ツール引数完了
```python
Stream Event: RawResponsesStreamEvent(
    data=ResponseFunctionCallArgumentsDoneEvent(
        arguments='{}',  # 完全な引数
        item_id='fc_68ae8db8b18c819097496bb68c17d3bd06980b07b64d526f'
    )
)
```

#### ツール出力アイテム完了
```python
Stream Event: RawResponsesStreamEvent(
    data=ResponseOutputItemDoneEvent(
        item=ResponseFunctionToolCall(
            call_id='call_WXXHRYxeBCIU72zUSGREMN22',
            name='get_current_time',
            status='completed'
        )
    )
)
```

#### ツール呼び出し完了（OpenAI側）
```python
Stream Event: RawResponsesStreamEvent(
    data=ResponseCompletedEvent(
        response=Response(
            output=[
                ResponseFunctionToolCall(
                    call_id='call_WXXHRYxeBCIU72zUSGREMN22',
                    name='get_current_time',
                    status='completed'
                )
            ]
        )
    )
)
```

### 1.3 ツール実行フェーズ（Agent SDK内部）

#### ツール呼び出し検出
```python
Stream Event: RunItemStreamEvent(
    name='tool_called',
    item=ToolCallItem(
        raw_item=ResponseFunctionToolCall(
            call_id='call_WXXHRYxeBCIU72zUSGREMN22',
            name='get_current_time',
            arguments='{}',
            status='completed'
        )
    )
)
```

#### ツール実行結果
```python
Stream Event: RunItemStreamEvent(
    name='tool_output',
    item=ToolCallOutputItem(
        raw_item={
            'call_id': 'call_WXXHRYxeBCIU72zUSGREMN22',
            'output': '2025-08-27 04:46:48 UTC',
            'type': 'function_call_output'
        },
        output='2025-08-27 04:46:48 UTC'
    )
)
```

### 1.4 アシスタント応答生成フェーズ

#### 2回目のレスポンス作成開始
```python
Stream Event: RawResponsesStreamEvent(
    data=ResponseCreatedEvent(
        response=Response(
            id='resp_68ae8db904788190a7b5ccb27c1bdd8606980b07b64d526f',
            status='in_progress'
        )
    )
)
```

#### メッセージアイテム追加
```python
Stream Event: RawResponsesStreamEvent(
    data=ResponseOutputItemAddedEvent(
        item=ResponseOutputMessage(
            id='msg_68ae8db9a06c819085ff2fb08b69418606980b07b64d526f',
            content=[],
            role='assistant',
            status='in_progress'
        )
    )
)
```

#### テキスト生成開始
```python
Stream Event: RawResponsesStreamEvent(
    data=ResponseContentPartAddedEvent(
        item_id='msg_68ae8db9a06c819085ff2fb08b69418606980b07b64d526f',
        part=ResponseOutputText(text='', type='output_text')
    )
)
```

#### テキスト増分イベント（文字単位）
```python
Stream Event: RawResponsesStreamEvent(
    data=ResponseTextDeltaEvent(
        delta='現在',
        item_id='msg_68ae8db9a06c819085ff2fb08b69418606980b07b64d526f'
    )
)

Stream Event: RawResponsesStreamEvent(
    data=ResponseTextDeltaEvent(
        delta='の',
        item_id='msg_68ae8db9a06c819085ff2fb08b69418606980b07b64d526f'
    )
)

Stream Event: RawResponsesStreamEvent(
    data=ResponseTextDeltaEvent(
        delta='時',
        item_id='msg_68ae8db9a06c819085ff2fb08b69418606980b07b64d526f'
    )
)

# ... 以下、文字単位で継続 ...
```

#### テキスト部分完了
```python
Stream Event: RawResponsesStreamEvent(
    data=ResponseTextDoneEvent(
        item_id='msg_68ae8db9a06c819085ff2fb08b69418606980b07b64d526f',
        text='現在の時刻は、協定世界時 (UTC) で2025年8月27日 04:46です。'
    )
)
```

#### コンテンツ部分完了
```python
Stream Event: RawResponsesStreamEvent(
    data=ResponseContentPartDoneEvent(
        item_id='msg_68ae8db9a06c819085ff2fb08b69418606980b07b64d526f',
        part=ResponseOutputText(
            text='現在の時刻は、協定世界時 (UTC) で2025年8月27日 04:46です。'
        )
    )
)
```

#### 出力アイテム完了
```python
Stream Event: RawResponsesStreamEvent(
    data=ResponseOutputItemDoneEvent(
        item=ResponseOutputMessage(
            id='msg_68ae8db9a06c819085ff2fb08b69418606980b07b64d526f',
            content=[ResponseOutputText(
                text='現在の時刻は、協定世界時 (UTC) で2025年8月27日 04:46です。'
            )],
            status='completed'
        )
    )
)
```

#### レスポンス完了
```python
Stream Event: RawResponsesStreamEvent(
    data=ResponseCompletedEvent(
        response=Response(
            output=[ResponseOutputMessage(...)],
            status='completed'
        )
    )
)
```

#### メッセージ出力作成完了
```python
Stream Event: RunItemStreamEvent(
    name='message_output_created',
    item=MessageOutputItem(
        raw_item=ResponseOutputMessage(
            id='msg_68ae8db9a06c819085ff2fb08b69418606980b07b64d526f',
            content=[ResponseOutputText(
                text='現在の時刻は、協定世界時 (UTC) で2025年8月27日 04:46です。'
            )],
            role='assistant',
            status='completed'
        )
    )
)
```

## 2. バックエンドでの処理と変換ロジック

### 2.1 イベントフィルタリング

```python
# backend/app/main.py:347-373
async for event in result.stream_events():
    # バックエンドで処理するイベントのみを選別
    if isinstance(event, RunItemStreamEvent):
        if event.name == "tool_called":
            # ツール呼び出し検出時の処理
        elif event.name == "tool_output":
            # ツール出力時の処理
            
    elif isinstance(event, RawResponsesStreamEvent):
        if isinstance(event.data, ResponseTextDeltaEvent):
            # テキスト増分時の処理
```

**処理される主要イベント**:
- `RunItemStreamEvent(name='tool_called')` → ツール情報を `active_tools` に保存
- `RunItemStreamEvent(name='tool_output')` → SSE形式でフロントエンドに送信
- `RawResponsesStreamEvent` + `ResponseTextDeltaEvent` → 文字単位でSSE送信

**無視されるイベント**:
- `AgentUpdatedStreamEvent` → エージェント初期化（処理対象外）
- `ResponseCreatedEvent`, `ResponseInProgressEvent` → OpenAI内部状態（処理対象外）
- `ResponseFunctionCallArgumentsDeltaEvent` → ツール引数生成（処理対象外）

### 2.2 ツール情報の一時保存メカニズム

#### なぜ一時保存が必要なのか

Agent SDKから送信される2つのイベントには**時間差問題**が存在します：

```python
# ⏰ 時刻 T1: ツール呼び出し検出
RunItemStreamEvent(name='tool_called')
├─ call_id: "call_WXXHRYxeBCIU72zUSGREMN22"  
├─ name: "get_current_time" ✅ ツール名が利用可能
└─ arguments: "{}"

# ⏰ 時刻 T2: ツール実行完了（T1より後）
RunItemStreamEvent(name='tool_output')  
├─ call_id: "call_WXXHRYxeBCIU72zUSGREMN22"  # 同じIDで紐付け
├─ output: "2025-08-27 04:46:48 UTC" ✅ 実行結果が利用可能
└─ name: ❌ ツール名が含まれていない
```

**問題点**: フロントエンドに送信するJSONには**ツール名と実行結果の両方**が必要ですが、`tool_output`イベント時点ではツール名が取得できません。

#### active_tools辞書による解決

```python
# backend/app/main.py:342, 354-355
active_tools = {}  # 一時保存用辞書

# Step 1: tool_called イベントでツール情報を保存
if event.name == "tool_called":
    tool_info = extract_tool_call_info(event)
    if tool_info:
        call_id, tool_name = tool_info
        active_tools[call_id] = tool_name
        # active_tools["call_WXXHRYxeBCIU72zUSGREMN22"] = "get_current_time"

# Step 2: tool_output イベントでツール情報を取得
elif event.name == "tool_output":
    call_id = event.item.raw_item["call_id"]
    tool_name = active_tools.get(call_id, "unknown")  # 保存済み情報を取得
    # tool_name = "get_current_time"
    
    # 使用後は削除してメモリ効率化
    active_tools.pop(call_id, None)
```

#### call_idによる一意性保証

```python
# 複数のツールが並行実行される場合
active_tools = {
    "call_WXXHRYxeBCIU72zUSGREMN22": "get_current_time",
    "call_DEF456A8B9C0D1E2F3G4H5": "calculate", 
    "call_ZYX987W6V5U4T3S2R1Q0": "web_search"
}

# 各ツールの完了時、call_idで正確に識別
tool_name = active_tools.get("call_DEF456A8B9C0D1E2F3G4H5")  # "calculate"
```

この仕組みにより、**ツール名と実行結果を組み合わせた完全なツール情報**をフロントエンドに送信できます。

### 2.3 SSE出力フォーマット

バックエンドで変換されたデータは、以下のSSE形式でフロントエンドに送信されます：

#### ツールイベント出力
```python
# 最終的なSSE出力フォーマット
"data: {\"role\": \"tool\", \"content\": \"{...}\", \"id\": \"call_WXXHRYxeBCIU72zUSGREMN22\", \"timestamp\": \"...\"}\n\n"
```

### 2.4 テキストイベントの変換プロセス

```python
# Agent SDK Raw Data (各文字ごと)
ResponseTextDeltaEvent(delta='現在', item_id='msg_xxx')
ResponseTextDeltaEvent(delta='の', item_id='msg_xxx')
ResponseTextDeltaEvent(delta='時', item_id='msg_xxx')

# Backend Processing (helper.py:137-145)
for each delta:
    content_event = {
        "role": "assistant",
        "content": delta,  # '現在', 'の', '時'...
        "id": assistant_id
    }
    yield f"data: {json.dumps(content_event, ensure_ascii=False)}\n\n"
```

## 3. フロントエンドに送信されるSSE データシーケンス

### 3.1 新規会話作成通知
```
data: {"type": "conversation_created", "conversation_id": "9de99a29-0aa0-4af4-9fba-bdeedc219572", "timestamp": "2025-08-27T04:37:14.008518+00:00"}
```

### 3.2 ツール実行完了通知
```
data: {"role": "tool", "content": "{\"tool_call_id\": \"call_WXXHRYxeBCIU72zUSGREMN22\", \"tool_name\": \"get_current_time\", \"output\": \"2025-08-27 04:46:48 UTC\", \"status\": \"success\"}", "id": "call_WXXHRYxeBCIU72zUSGREMN22", "timestamp": "2025-08-27T04:46:48.291408+00:00"}
```

### 3.3 アシスタントテキスト増分（リアルタイム）
```
data: {"role": "assistant", "content": "現在", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "の", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "時", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "刻", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "は", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "、", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "協", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "定", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "世界", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "時", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": " (", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "UTC", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": ")", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": " ", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "で", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "202", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "5", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "年", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "8", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "月", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "27", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "日", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": " ", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "04", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": ":", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "46", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "です", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}

data: {"role": "assistant", "content": "。", "id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}
```

### 3.4 ストリーミング完了通知
```
event: done
data: {"id": "a52ab531-9bd9-49c3-8e61-ec2ecf36403e"}
```

## 4. フロントエンドでの受信と処理

### 4.1 ツールイベントの処理
```typescript
// frontend/src/pages/Chat.tsx:189-201
case 'tool':
  setMessages((prev) => [
    ...prev,
    {
      id: data.id,                    // call_WXXHRYxeBCIU72zUSGREMN22
      role: 'tool',
      content: data.content,          // JSON文字列（構造化データ）
      timestamp: data.timestamp,      // 2025-08-27T04:46:48.xxx+00:00
    },
  ]);
  break;
```

### 4.2 ストリーミングテキストの蓄積
```typescript
// frontend/src/pages/Chat.tsx:202-218
case 'assistant':
  setStreamingMessage((prev) => {
    if (!prev) {
      return {
        id: data.id,
        content: data.content,        // 初回: '現在'
        isStreaming: true,
      };
    }
    return {
      ...prev,
      content: prev.content + data.content,  // 蓄積: '現在' + 'の' + '時'...
    };
  });
  break;
```

### 4.3 完了時の最終処理
```typescript
// frontend/src/pages/Chat.tsx:237-255
if (currentEvent === 'done') {
  setStreamingMessage((prev) => {
    if (prev) {
      setMessages((m) => [
        ...m,
        {
          id: data.id,
          role: 'assistant',
          content: prev.content,        // 完全なテキスト
          timestamp: new Date().toISOString(),
        },
      ]);
    }
    return null;  // ストリーミング状態解除
  });
  setIsLoading(false);
}
```

## 5. データ変換の完全なフロー図解

### 5.1 ツール実行の変換フロー

```
Agent SDK → Backend Processing → SSE Output → Frontend State

[Agent初期化]
AgentUpdatedStreamEvent
         ↓
    (無視される)

[ツール決定フェーズ - OpenAI内部処理]
ResponseCreatedEvent
ResponseOutputItemAddedEvent(ToolCall)
ResponseFunctionCallArgumentsDeltaEvent
ResponseCompletedEvent
         ↓
    (無視される)

[ツール実行フェーズ - Agent SDK内部処理]
RunItemStreamEvent(name='tool_called')
    call_id: call_WXXHRYxeBCIU72zUSGREMN22
    name: get_current_time
         ↓
active_tools[call_id] = tool_name  ← バックエンド保存
         ↓
RunItemStreamEvent(name='tool_output')
    call_id: call_WXXHRYxeBCIU72zUSGREMN22
    output: 2025-08-27 04:46:48 UTC
         ↓
{                                   ← SSE変換処理
  "role": "tool",
  "content": "{\"tool_name\": \"get_current_time\", ...}",
  "id": "call_WXXHRYxeBCIU72zUSGREMN22",
  "timestamp": "2025-08-27T04:46:48.xxx+00:00"
}
         ↓
messages.push({                    ← フロントエンド追加
  id: "call_WXXHRYxeBCIU72zUSGREMN22",
  role: "tool",
  content: "{\"tool_name\": \"get_current_time\", ...}",
  timestamp: "2025-08-27T04:46:48.xxx+00:00"
})
```

### 5.2 テキスト生成の変換フロー

```
Agent SDK → Backend → Frontend

ResponseTextDeltaEvent(delta='現在') → SSE変換 → streamingMessage更新
ResponseTextDeltaEvent(delta='の')   → SSE変換 → 文字連結('現在の')
... (文字単位で継続) ...
ResponseTextDoneEvent → event:done → 最終メッセージ保存

ポイント: 文字単位リアルタイム更新 → 完了時一括保存
```

## 6. パフォーマンスとリアルタイム性

### 6.1 0遅延処理
- **Agent SDK** → **Backend変換** → **SSE送信** は同期的に即座実行
- **フロントエンド受信** → **状態更新** → **DOM反映** も即座実行

### 6.2 メモリ効率
- **Backend**: イベント単位処理でメモリ使用量最小化
- **Frontend**: ストリーミング中は専用の`streamingMessage`状態を使用
- **Database**: ストリーミング完了後にまとめて保存

### 6.3 エラー処理と復旧
- **Agent SDKイベントエラー**: `try-except`でエラー時は無視継続
- **JSON解析エラー**: フロントエンドでフォールバック処理
- **SSE接続エラー**: 自動再接続機能

この実装により、Agent SDKの詳細なストリーミングイベントを効率的にリアルタイム配信し、優れたユーザーエクスペリエンスを実現しています。