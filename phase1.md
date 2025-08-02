# Phase 1: メッセージデータ構造のシンプル化

## 概要

現在の複雑な `tool_metadata` 構造を廃止し、OpenAI API標準準拠の `role:tool` メッセージ形式に移行することで、データ構造の大幅なシンプル化を実現する。
また、ツールを利用しようとしているかどうかはフロントエンドに送信しない


## 現状の問題点

### 複雑なデータ構造
```python
# 現在の複雑な tool_metadata 構造
tool_metadata = {
    "tools_used": [
        {
            "name": "get_weather",
            "input": {"location": "東京"},
            "output": "晴れ、15℃",
            "status": "success",
            "execution_time_ms": 1234
        }
    ],
    "summary": {
        "total_tools": 1,
        "total_time_ms": 1234,
        "success_count": 1,
        "error_count": 0
    }
}
```

### 複雑な変換処理
- `convert_tool_metadata_to_executions()` 関数（main.py:252-290）
- フロントエンドでの複雑な `toolExecutions` 処理
- Phase 1-2 で蓄積された技術的負債

## 提案するソリューション

### OpenAI API 2025年仕様準拠

**調査結果：**
- ✅ `role:tool` は正式サポート済み
- ✅ openai-agents-python SDK で `Converter.items_to_messages()` による標準変換対応
  - SDKは、ツール出力（`ResponseFunctionToolCallOutput`）を `role: "tool"`、`tool_call_id`、`content` を含む `ChatCompletionToolMessageParam` に変換します。
- ✅ API version: `2025-02-01-preview`（最新）

### 超シンプル化アプローチ：全情報をcontent統一

**データ構造例：**

```python
# role:tool メッセージ
{
  "id": "msg3",
  "role": "tool",
  # toolだけcontentがJSON文字列
  "content": json.dumps({
    "tool_call_id": "call_abc123",
    "tool_name": "get_weather",
    "arguments": {"location": "東京"},
    "output": "晴れ、15℃",
    "execution_time_ms": 1234,
    "status": "success"
  }),
  "timestamp": "2025-01-15T10:30:22.000Z"
}

# role:assistant メッセージ（プレーンテキストのみ）
{
  "id": "msg4",
  "role": "assistant",
  "content": "現在の東京は晴れで、気温は15℃です。",  # プレーンテキスト
  "timestamp": "2025-01-15T10:30:25.000Z"
}

# role:user メッセージ（プレーンテキストのまま）
{
  "id": "msg1",
  "role": "user",
  "content": "今日の東京の天気を教えて",  # プレーンテキスト
  "timestamp": "2025-01-15T10:30:15.000Z"
}
```

## データベース変更

### Message テーブル（最小限変更）

**変更前：**
```python
class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String, nullable=False)  # "user" | "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime)

    # Phase 1-2で追加された複雑な構造
    tool_metadata = Column(JSON, nullable=True)
    has_detailed_executions = Column(Boolean, default=False)
    tool_executions = relationship("ToolExecution", ...)
```

**変更後：**
```python
class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String, nullable=False)  # "user" | "assistant" | "tool"
    content = Column(Text, nullable=False)  # user/assistant: プレーンテキスト、tool: JSON文字列
    created_at = Column(DateTime)

    # リレーション
    conversation = relationship("Conversation", back_populates="messages")
```

### 削除対象

**🗑️ 未使用になるカラム・テーブル：**
- `Message.tool_metadata` カラム（JSON）
- `Message.has_detailed_executions` カラム（Boolean）
- `Message.tool_executions` リレーション
- `ToolExecution` テーブル全体
- `models/tool_execution.py` ファイル


## チャット時のSSEでバックエンドからフロントエンドに送信されるデータ

`openai-agents-python` SDKは、`Runner.run_streamed().stream_events()` を通じて `StreamEvent` オブジェクトをストリームします。これには主に `RawResponsesStreamEvent` と `RunItemStreamEvent` があります。

*   **`RunItemStreamEvent`**: より高レベルなイベントで、完全なアイテム（メッセージやツール出力）が生成されたことを示します。SSEストリーミングには主にこれを使用します。
    *   `item.type == "tool_call_output_item"`: ツールの実行結果。`tool_call_id`、`tool_name`、`output`、`status` などを含みます。
    *   `item.type == "message_item"` (role: assistant): アシスタントの応答。`content` をチャンク単位で含みます。

### tool利用なしの場合

#### データ構造

```
data: {"role":"assistant","content":"こ","id":"ed0aadaa-b8a2-4eab-ad89-59db719edc62"}
data: {"role":"assistant","content":"ん","id":"ed0aadaa-b8a2-4eab-ad89-59db719edc62"}
data: {"role":"assistant","content":"に","id":"ed0aadaa-b8a2-4eab-ad89-59db719edc62"}
data: {"role":"assistant","content":"ち","id":"ed0aadaa-b8a2-4eab-ad89-59db719edc62"}
data: {"role":"assistant","content":"は","id":"ed0aadaa-b8a2-4eab-ad89-59db719edc62"}
done: {"id":"ed0aadaa-b8a2-4eab-ad89-59db719edc62"}
```

#### フロントエンド側の処理

ユーザーの入力が送信された後、SSEでデータが返ってくるまでは 「(スピナー) 解答を生成しています」を表示する
data: 〜〜のJSONを随時パースしてappnendしながらレスポンスを画面に表示する、末尾にカーソルを点滅表示する
done: 〜を受け取った場合はレスポンスの画面表示終了


### tool利用ありの場合

#### データ構造

```
data: {"role": "tool", "content": "{"tool_call_id": "call_kp3GvaOsZI8MVlvHLCaUfD10", "tool_name": "get_current_time", "output": "2025-08-01 22:23:55 UTC", "status": "success"}", "id": "53fa37ac-ccc8-41f0-a2b7-7716d5677c12"}
data: {"role":"assistant","content":"こ","id":"ed0aadaa-b8a2-4eab-ad89-59db719edc62"}
data: {"role":"assistant","content":"ん","id":"ed0aadaa-b8a2-4eab-ad89-59db719edc62"}
data: {"role":"assistant","content":"に","id":"ed0aadaa-b8a2-4eab-ad89-59db719edc62"}
data: {"role":"assistant","content":"ち","id":"ed0aadaa-b8a2-4eab-ad89-59db719edc62"}
data: {"role":"assistant","content":"は","id":"ed0aadaa-b8a2-4eab-ad89-59db719edc62"}
done: {"id":"ed0aadaa-b8a2-4eab-ad89-59db719edc62"}
```

#### フロントエンド側の処理

ユーザーの入力が送信された後、SSEでデータが返ってくるまでは 「(スピナー) 解答を生成しています」を表示する
data: role: toolの場合はいったん何もレンダリングせず、会話セッションのstateに値を追加する
data: role: assistantの場合は〜〜のJSONを随時パースしてappnendしながらレスポンスを画面に表示する、末尾にカーソルを点滅表示する
done: 〜を受け取った場合はレスポンスの画面表示終了
その後、いったん避けたrole: toolの内容を会話セッションのステートからパースしてassistantのレスポンスの下にツール名と結果を表示する


## フロントエンド変更

### 統一的JSON処理ロジック

```typescript
interface MessageContent {
  // user メッセージ
  text?: string;

  // assistant メッセージ
  tool_calls?: ToolCall[];

  // tool メッセージ
  tool_call_id?: string;
  tool_name?: string;
  arguments?: Record<string, any>;
  output?: string;
  execution_time_ms?: number;
  status?: 'success' | 'error';
}

const parseMessageContent = (message: Message): MessageContent => {
  if (message.role === 'tool') {
    try {
      return JSON.parse(message.content);
    } catch {
      console.error('Failed to parse tool message content');
      return {};
    }
  }

  if (message.role === 'assistant') {
    try {
      // JSON形式の場合（tool_callsあり）
      return JSON.parse(message.content);
    } catch {
      // プレーンテキストの場合
      return { text: message.content };
    }
  }

  // user メッセージはプレーンテキスト
  return { text: message.content };
};
```

### 表示ロジック簡素化

```typescript
const renderMessage = (message: Message) => {
  const content = parseMessageContent(message);

  switch (message.role) {
    case 'user':
      return <UserMessage text={content.text || message.content} />;

    case 'assistant':
      return (
        <AssistantMessage
          text={content.text || message.content}
          toolCalls={content.tool_calls}
        />
      );

    case 'tool':
      return (
        <ToolMessage
          toolName={content.tool_name}
          output={content.output}
          status={content.status}
        />
      );
  }
};
```

## バックエンド実装

### openai-agents-python SDK活用

```python
from agents.models.chatcmpl_converter import Converter

async def stream_chat(conversation_id, request, ...):
    # Agents SDK でストリーミング実行
    result = Runner.run_streamed(chat_agent, api_messages)

    # deepwikiの調査結果に基づき、result.to_input_list()が永続化に最も適した完全な会話履歴を提供します。
    # 完了後に標準メッセージ形式に変換
    openai_messages = Converter.items_to_messages(result.to_input_list())

    # 各メッセージをデータベースに保存
    # deepwikiの調査結果に基づき、ストリーミング完了後にまとめて保存します。
    for msg in openai_messages:
        if msg['role'] == 'tool':
            # tool メッセージは JSON文字列で保存
            content = json.dumps({
                "tool_call_id": msg['tool_call_id'],
                "tool_name": msg.get('name', ''),
                "output": msg['content'],
                "status": "success"
            })
        elif msg['role'] == 'assistant' and msg.get('tool_calls'):
            # tool_calls がある assistant メッセージは JSON文字列で保存
            content = json.dumps({
                "text": msg.get('content', ''),
                "tool_calls": msg['tool_calls']
            })
        else:
            # user メッセージや通常の assistant メッセージはプレーンテキスト
            content = msg['content']

        db_message = Message(
            conversation_id=conv.id,
            role=msg['role'],
            content=content
        )
        db.add(db_message)
```

### 削除される複雑な処理

- `StreamToolTracker` クラス（main.py:57-106）
- `convert_tool_metadata_to_executions()` 関数（main.py:252-290）
- 複雑なSSEイベント処理ロジック
- ツール実行状態管理の重複処理

## 実装効果

### 🎯 シンプル化メトリクス

**データベース：**
- カラム削除：2個
- テーブル削除：1個
- リレーション削除：1個
- ファイル削除：`tool_execution.py`

**バックエンドコード：**
- 複雑な変換処理：**完全削除**
- メンテナンス対象行数：**90%削減**
- デバッグ容易性：**大幅向上**

**フロントエンド：**
- 型定義：**大幅簡素化**
- 状態管理：**統一化**
- 表示ロジック：**一本化**

### 🚀 開発効率向上

**⚡ 実装コスト：最小**
- データベースマイグレーション：role列の制約緩和のみ
- バックエンドロジック変更：tool_metadata削除 + JSON.dumps()
- フロントエンド変更：parseMessageContent()関数1つ追加

**🎯 一貫性：最高**
- すべてのメッセージが同じテーブル、同じ構造
- role による分岐だけでシンプルな処理
- OpenAI標準完全準拠

**🔧 拡張性：抜群**
- 新しいツール情報 → JSONに項目追加
- 新しいrole → 同じパターンで対応
- 外部システム連携 → 標準形式そのまま

## 実装順序

1. **Phase 1.1: データベースマイグレーション**
   - role列の制約変更（"tool"追加）
   - 不要カラム・テーブルの削除

2. **Phase 1.2: バックエンド実装**
   - openai-agents-python SDK統合
   - 複雑な処理ロジック削除
   - 標準メッセージ形式での保存

3. **Phase 1.3: フロントエンド対応**
   - parseMessageContent()実装
   - 表示ロジック統一化
   - 既存UIコンポーネント調整

4. **Phase 1.4: テスト・検証**
   - 既存データとの互換性確認
   - SSEストリーミング動作確認
   - パフォーマンス検証

## 期待される成果

- **コード保守性：劇的向上**
- **開発速度：大幅向上**
- **バグ発生率：大幅削減**
- **新機能開発：加速**
- **OpenAI仕様追従：容易**

この Phase 1 により、アプリケーションの技術的負債を大幅に削減し、今後の開発効率を飛躍的に向上させることができる。

## アプリケーション機能への包括的影響調査

Phase1変更による既存機能への影響を包括的に調査し、必要な修正内容を特定した。

### 調査対象機能

1. **新しい会話開始機能**
2. **複数回やり取り・SSEストリーミング機能**
3. **過去の会話履歴復元・再会機能**
4. **フロントエンドの画面表示・UI機能**
5. **APIエンドポイント全体**

---

## 機能別影響分析と修正内容

### 1. 新しい会話開始機能

**影響度：❌ 影響なし**

- `/api/conversations` POST（main.py:209-220）
- 単純にConversationエンティティを作成するのみ
- **修正不要**

### 2. 複数回やり取り・SSEストリーミング機能

**影響度：🔥 大幅修正必要**

#### 現在の実装問題点：
```python
# main.py:383-386 - 履歴準備の問題
api_messages = [
    {"role": m.role, "content": m.content} for m in conv.messages
]
```

---

## Phase1実装失敗から得られた教訓

本リファクタリングの初期実装において、アプリケーションが動作しなくなる事態が発生した。その原因分析と再発防止策を以下に記録する。

### 失敗の根本原因

失敗の根本原因は、**「リファクタリングの範囲と手順の定義が曖昧なまま、複数の関心事を同時に変更しようとした」**ことにある。具体的には以下の3点が挙げられる。

1.  **段階的リファクタリングの欠如**: データ構造、リアルタイム処理、DBモデル、UIロジックという4つの大きな変更を一度に実施しようとしたため、各コンポーネント間の整合性が取れなくなり、破綻した。
2.  **責務の混在**: バックエンドの単一関数(`stream_chat`)が、AI通信、SSE送信、DB保存、データ変換など、あまりに多くの責務を負い、コードが複雑化しデバッグ不能に陥った。
3.  **F/EとB/Eの密結合**: フロントエンドが、バックエンドから送られるSSEイベントの「種類」と「順序」に強く依存するロジックだったため、少しの変更で全体が機能しなくなった。

### 今後の開発で遵守すべき教訓

この失敗から得られた教訓を、今後の開発における行動規範とする。

#### ✅ 教訓1：リファクタリングは「小さく、段階的に」進める
大規模な変更は、必ず独立して検証可能な小さなステップに分割する。各ステップが完了するたびに、アプリケーションが正常に動作することを確認する。

**悪い例**: DB、バックエンド、フロントエンドを一度に変更する。
**良い例**: 
1.  まずDBスキーマだけを変更し、マイグレーションを適用する。
2.  次にバックエンドのデータ保存/取得ロジックを新スキーマに対応させる（APIのインターフェースは変えない）。
3.  最後にフロントエンドを新しいAPIの形式に対応させる。

#### ✅ 教訓2：単一責任の原則（SRP）を徹底する
一つの関数やクラスには、一つの明確な責任だけを持たせる。これにより、コードの可読性、テスト容易性、保守性が向上する。

**悪い例**: `stream_chat`関数がAIとの通信からDB操作まで全てを行う。
**良い例**: 
- `prepare_api_messages()`: APIリクエスト用のメッセージ履歴を準備する。
- `save_messages_to_db()`: 会話のメッセージをデータベースに保存する。
- `stream_chat()`: SSEストリーミングの責務に集中する。

#### ✅ 教訓3：F/EとB/Eは「データ構造」で疎結合に保つ
フロントエンドとバックエンドの間の通信は、複雑なイベントの「順序」や「種類」に依存させるべきではない。バックエンドは完成した**状態（データ構造）**を送信し、フロントエンドはそれを受け取ってレンダリングする、というシンプルな契約を基本とする。

**悪い例**: フロントエンドが`tool_start`→`tool_complete`→`content`というイベント順を前提としてUIを構築する。
**良い例**: バックエンドは完成した`Message`オブジェクト（`role: 'tool'`や`role: 'assistant'`）を送信する。フロントエンドは受信した`Message`オブジェクトの`role`を見て、適切に表示する。

これらの教訓を遵守することで、将来の機能開発やリファクタリングにおけるリスクを大幅に低減し、開発効率とコード品質の向上を目指す。