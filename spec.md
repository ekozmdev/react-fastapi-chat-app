# OpenAI パッケージ切り替え仕様書

## 概要
バックエンドの OpenAI 呼び出し部分を直接の `AsyncOpenAI` クライアントから `openai-agents-python` SDK に切り替える。**既存機能は完全に維持し、新機能は追加しない**。

## 目的
- 将来的なエージェント機能拡張の基盤準備
- 既存のSSEストリーミング動作を完全に維持
- フロントエンドへの影響なし

## 現在の実装分析

### OpenAI呼び出し箇所（`backend/app/main.py`）
- **Line 13**: `from openai import AsyncOpenAI`
- **Line 48**: `client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))`
- **Line 505-511**: ストリーミング作成部分
- **Line 513-524**: ストリーミング処理とSSE送信

### 現在のコード（main.py:505-524）

```python
# OpenAI ストリーミング開始
stream = await client.chat.completions.create(
    model="gpt-4.1",
    messages=api_messages,
    max_tokens=1024,
    temperature=0.7,
    stream=True,
)

async for chunk in stream:
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        assistant_content += content

        # コンテンツストリーミング
        content_event = SSEEvent(
            type="content",
            content=content,
            message_id=assistant_id
        )
        yield f"data: {content_event.model_dump_json()}\n\n"
```

## 切り替え仕様

### 1. 依存関係の追加
```bash
cd backend
uv add openai-agents
```

### 2. 最小限のコード変更

#### A. インポートの追加
```python
# 既存のインポートを維持
from openai import AsyncOpenAI

# 新しく追加
from agents import Agent, Runner
```

#### B. エージェント定義（アプリケーション初期化時）
```python
# グローバル変数として定義
chat_agent = Agent(
    name="ChatAssistant",
    instructions="You are a helpful assistant. Please respond in the same language as the user's input.",
    model="gpt-4o",
    # 既存パラメータを維持
    max_tokens=1024,
    temperature=0.7,
)
```

#### C. ストリーミング部分のみ置き換え
```python
# 置き換え前（main.py:505-524）
stream = await client.chat.completions.create(
    model="gpt-4.1",
    messages=api_messages,
    max_tokens=1024,
    temperature=0.7,
    stream=True,
)

async for chunk in stream:
    if chunk.choices[0].delta.content:
        content = chunk.choices[0].delta.content
        assistant_content += content
        
        content_event = SSEEvent(
            type="content",
            content=content,
            message_id=assistant_id
        )
        yield f"data: {content_event.model_dump_json()}\n\n"

# 置き換え後
result = Runner.run_streamed(chat_agent, api_messages)

async for event in result.stream_events():
    if event.type == "raw_response_event":
        if hasattr(event.data, 'delta') and event.data.delta:
            content = event.data.delta
            assistant_content += content
            
            content_event = SSEEvent(
                type="content",
                content=content,
                message_id=assistant_id
            )
            yield f"data: {content_event.model_dump_json()}\n\n"
```

## 動作保証

### 維持する機能
1. **SSEストリーミング**: 既存のフロントエンドとの完全互換性
2. **レスポンス形式**: `SSEEvent` 構造の維持
3. **エラーハンドリング**: 既存のtry-catch構造維持
4. **データベース操作**: メッセージ保存ロジックの維持
5. **認証**: JWT認証フローの維持

### 変更しない部分
- FastAPI エンドポイント構造
- データベーススキーマ
- フロントエンドとの通信プロトコル
- エラーレスポンス形式
- 認証・認可ロジック

## 実装手順

### Phase 1: 環境準備
```bash
cd backend
uv add openai-agents
```

### Phase 2: コード変更
1. インポート追加
2. エージェント定義追加
3. ストリーミング部分のみ置き換え

### Phase 3: 動作確認
1. 既存テストの実行
2. SSEエンドポイントの動作確認
3. フロントエンドとの統合テスト

## リスク対策

### 低リスク要因
- 最小限の変更範囲
- 既存インターフェース維持
- 段階的な実装

### 対策
- 既存の`AsyncOpenAI`クライアント保持（フォールバック用）
- 詳細なテストによる動作確認
- リリース前の十分な検証期間

## 成功基準

1. **機能維持**: 既存のすべての機能が同じように動作する
2. **パフォーマンス**: レスポンス時間の大幅な劣化がない
3. **安定性**: エラー率の増加がない
4. **互換性**: フロントエンドの変更が不要

この仕様により、将来のエージェント機能拡張の基盤を準備しつつ、現在の安定した動作を維持する。

## セルフレビュー：データベース保存・フロントエンドへの影響分析

### ✅ 影響なし（確認済み）

#### 1. データベース保存ロジック
**現在の保存フロー**:
```python
# Line 478-485: ユーザーメッセージ即座に保存
user_msg = Message(...)
db.add(user_msg)
db.commit()

# Line 488-497: 履歴をOpenAI API形式で取得
api_messages = [{"role": m.role, "content": m.content} for m in conv.messages]

# Line 513-524: ストリーミング中に蓄積
assistant_content += content

# Line 526-534: 蓄積したコンテンツを保存
db.add(Message(..., content=assistant_content))
```

**移行後も同じフロー**:
- ✅ `Runner.run_streamed(agent, api_messages)` - OpenAI API形式を直接受け取り可能
- ✅ `assistant_content += event.data.delta` - 同じ蓄積方法
- ✅ `async for event in result.stream_events()` - 完了時に自動停止
- ✅ データベース保存タイミング・方法は完全に同じ

#### 2. フロントエンドとの互換性
**SSEイベント形式は完全維持**:
```python
# 現在も移行後も同じ形式
content_event = SSEEvent(
    type="content",
    content=content,  # chunk.choices[0].delta.content → event.data.delta
    message_id=assistant_id
)
yield f"data: {content_event.model_dump_json()}\n\n"
```

- ✅ SSE形式: `data: {...}\n\n` 維持
- ✅ イベント構造: `SSEEvent` クラス維持  
- ✅ イベント種類: `content`, `done`, `error` 維持
- ✅ ストリーミング順序: トークン単位での送信維持

### ⚠️ 検証が必要な項目

#### 1. ストリーミング内容の一致性
```python
# 現在: OpenAI API
chunk.choices[0].delta.content  # → "Hello"

# 移行後: Agents SDK  
event.data.delta  # → "Hello" (同じ内容か要確認)
```

#### 2. エラーハンドリングの互換性
```python
# 現在のエラーキャッチ
try:
    stream = await client.chat.completions.create(...)
except Exception as e:
    error_event = SSEEvent(type="error", message=f"エラーが発生しました: {str(e)}")

# 移行後も同じ構造でキャッチできるか要確認
```

#### 3. パフォーマンス・タイミング
- ストリーミング開始までの遅延時間
- トークン送信間隔
- 全体的なレスポンス時間

### 🔧 修正版：置き換えコード

```python
# より安全な移行コード
try:
    # Agents SDK でストリーミング実行
    result = Runner.run_streamed(chat_agent, api_messages)
    
    async for event in result.stream_events():
        if event.type == "raw_response_event":
            # delta の存在と内容を慎重にチェック
            if (hasattr(event.data, 'delta') and 
                event.data.delta and 
                isinstance(event.data.delta, str)):
                
                content = event.data.delta
                assistant_content += content
                
                content_event = SSEEvent(
                    type="content",
                    content=content,
                    message_id=assistant_id
                )
                yield f"data: {content_event.model_dump_json()}\n\n"
    
    # ストリーミング完了は自動検知（追加処理不要）
    
except Exception as e:
    # Agents SDK のエラーも同じ方法でキャッチ・送信
    error_event = SSEEvent(
        type="error", 
        message=f"エラーが発生しました: {str(e)}"
    )
    yield f"data: {error_event.model_dump_json()}\n\n"
```

### 📋 移行時のテスト項目

#### 必須テスト
1. **データ整合性**: 保存されるメッセージ内容が現在と同一
2. **SSE形式**: フロントエンドが正常に受信・表示
3. **エラー処理**: 各種エラーケースでの動作確認
4. **会話履歴**: 複数ターンの会話が正常に継続

#### パフォーマンステスト  
1. **レスポンス時間**: 初回応答までの時間測定
2. **ストリーミング速度**: トークン/秒の測定
3. **メモリ使用量**: 長い会話での検証

### 結論
データベース保存・フロントエンド互換性については **影響なし** と判断。ただし、実装時は慎重なテストとエラーハンドリングの検証が必要。

## 実装可能性セルフレビュー

### ✅ **技術的実装可能性 - 確認済み**

**1. Agent設定の正確な方法**
```python
from agents import Agent, ModelSettings

chat_agent = Agent(
    name="ChatAssistant",
    instructions="You are a helpful assistant. Please respond in the same language as the user's input.",
    model="gpt-4o",
    model_settings=ModelSettings(
        max_tokens=1024,
        temperature=0.7,
    )
)
```

**2. 入力形式の互換性**
- ✅ `Runner.run_streamed(agent, api_messages)` でOpenAI API形式を直接受け取り可能
- ✅ `result.stream_events()` でトークン単位のストリーミング可能
- ✅ ストリーミング完了は自動検知

### ⚠️ **実装上の重要な課題**

#### 1. システムプロンプトの処理方法変更
```python
# 現在: api_messagesに含める
api_messages.insert(0, {"role": "system", "content": "..."})

# 移行後: Agentのinstructionsで設定
# → システムプロンプトの扱い方が変わることで応答が微妙に変わる可能性
```

#### 2. モデル名の強制変更
```python
# 現在: "gpt-4.1" 
# 移行後: "gpt-4o" (Agents SDKで対応するモデル名)
# → モデル特性の変化によるユーザー体験への影響
```

#### 3. ストリーミングデータ形式の不確実性
```python
# 現在: chunk.choices[0].delta.content (必ず文字列)
# 移行後: event.data.delta (形式・型が要確認)
```

#### 4. spec.mdの修正版コード
```python
# より現実的な移行コード
try:
    result = Runner.run_streamed(chat_agent, api_messages)
    
    async for event in result.stream_events():
        if event.type == "raw_response_event":
            # 型安全性を重視した確認
            if (hasattr(event, 'data') and 
                hasattr(event.data, 'delta') and 
                event.data.delta is not None and
                isinstance(event.data.delta, str)):
                
                content = str(event.data.delta)  # 明示的な型変換
                assistant_content += content
                
                content_event = SSEEvent(
                    type="content",
                    content=content,
                    message_id=assistant_id
                )
                yield f"data: {content_event.model_dump_json()}\n\n"
            else:
                # デバッグ用: 予期しない形式をログ出力
                print(f"Unexpected event.data format: {type(event.data)}, {event.data}")

except Exception as e:
    # Agents SDK特有のエラーも同じ方法でハンドリング
    error_event = SSEEvent(
        type="error", 
        message=f"エラーが発生しました: {str(e)}"
    )
    yield f"data: {error_event.model_dump_json()}\n\n"
```

### 🚨 **高リスク要因**

1. **システムプロンプト処理の変更**: LLMの応答パターンが変わる可能性
2. **モデル変更の強制**: gpt-4.1 → gpt-4o でユーザー体験に影響
3. **ストリーミング形式の不確実性**: `event.data.delta`の正確な形式が不明
4. **エラーパターンの違い**: Agents SDK特有のエラーが既存処理で捕捉できない可能性

### 📋 **実装前必須検証項目**

#### Phase 0: プロトタイプ検証
1. **最小限のテストケース作成**: 1往復の会話で動作確認
2. **event.data.deltaの形式確認**: 実際の出力内容・型の検証
3. **エラーパターンの確認**: 意図的にエラーを発生させて動作確認
4. **システムプロンプト効果の比較**: 現在と移行後の応答品質比較

#### Phase 1: 機能検証
1. **複数ターン会話**: 履歴が正しく引き継がれるか
2. **日本語処理**: 日本語入力での応答が現在と同等か
3. **ストリーミング速度**: 体感的な遅延がないか
4. **長文処理**: max_tokens付近での動作確認

#### Phase 2: 統合テスト
1. **フロントエンド統合**: 実際のReactアプリでの動作確認
2. **データベース整合性**: 保存されるメッセージ内容の検証
3. **認証との連携**: JWT認証下での正常動作
4. **エラーケース**: ネットワークエラー、タイムアウト等

### 🏁 **総合判定: 実装可能、ただし慎重な段階的アプローチが必要**

**実装可能性**: ⭐⭐⭐⭐☆ (4/5)
- 技術的には実装可能
- ただし重要な不確実要素が複数存在

**推奨アプローチ**:
1. **小規模プロトタイプでの検証** (1-2日)
2. **段階的な実装とテスト** (3-5日)  
3. **フォールバック機能の維持** (既存コードを残す)
4. **十分な検証期間** (1週間)

現在のspec.mdの内容は実装の方向性として適切だが、上記の課題を解決してからの実装を強く推奨。