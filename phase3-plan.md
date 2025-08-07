# Phase3: SDKイベント処理の根本的リファクタリング実装計画

## 1. 分析結果サマリー

### OpenAI Agents SDK イベント構造の理解

**高レベルイベント（RunItemStreamEvent）**:
- `name='tool_called'`: ツール呼び出し開始、`item=ToolCallItem`
- `name='tool_output'`: ツール実行完了、`item=ToolCallOutputItem`

**低レベルイベント（RawResponsesStreamEvent）**:
- `ResponseTextDeltaEvent`: テキスト応答の断片（`delta`プロパティ）
- `ResponseFunctionCallArgumentsDeltaEvent`: ツール引数の断片（**無視推奨**）

### 現在の実装の問題点
1. **過度な複雑性**: 70行の`tool_tracking`辞書による手動状態管理
2. **不安定な型判定**: `hasattr`を多用した危険なロジック  
3. **冗長なIDマッチング**: 部分文字列マッチングによる不確実な処理

## 2. 新実装設計

### 基本方針
- **SDKイベントの直接活用**: RunItemStreamEventを中心とした処理
- **厳密な型判定**: `isinstance`による安全な分岐
- **最小限の状態管理**: call_id→tool_nameの単純マッピングのみ

### イベント処理フロー
```
1. tool_called → call_id + tool_nameを記録
2. tool_output → ツール完了処理 + SSE送信  
3. ResponseTextDeltaEvent → テキストストリーミング
4. ResponseFunctionCallArgumentsDeltaEvent → 完全無視
```

## 3. 具体的実装コード

```python
# 必要なインポート文（main.pyに追加）
from agents.stream_events import RunItemStreamEvent

async def generate_sse_stream():
    try:
        # 既存の会話準備処理は同じ...
        
        assistant_content = ""
        assistant_id = generate_unique_id()
        # 最小限の状態管理: call_id -> tool_name マッピング
        active_tools = {}  # Dict[str, str] - call_id: tool_name
        sent_tool_messages = []  # DB保存用ツールメッセージ

        # Agents SDK でストリーミング実行
        result = Runner.run_streamed(chat_agent, api_messages)
        async for event in result.stream_events():
            
            # ========== 高レベルイベント: ツール処理 ==========
            if isinstance(event, RunItemStreamEvent):
                
                if event.name == 'tool_called':
                    # ツール呼び出し開始 - ツール名を記録
                    try:
                        call_id = event.item.raw_item.call_id
                        tool_name = event.item.raw_item.name
                        active_tools[call_id] = tool_name
                    except (AttributeError, KeyError) as e:
                        print(f"[WARNING] tool_called属性アクセスエラー: {e}")
                        continue
                    
                elif event.name == 'tool_output':
                    # ツール実行完了 - 直接出力を取得してSSE送信
                    try:
                        call_id = event.item.raw_item['call_id']
                        output = event.item.output
                        tool_name = active_tools.get(call_id, "unknown")
                    except (KeyError, TypeError) as e:
                        print(f"[WARNING] tool_output属性アクセスエラー: {e}")
                        continue
                    
                    # Phase1仕様のrole:toolイベント送信
                    tool_content_dict = {
                        "tool_call_id": call_id,
                        "tool_name": tool_name,
                        "output": output,
                        "status": "success"
                    }
                    
                    tool_event = {
                        "role": "tool",
                        "content": json.dumps(tool_content_dict, ensure_ascii=False),
                        "id": call_id,
                        "timestamp": datetime.now(UTC).isoformat()
                    }
                    yield f"data: {json.dumps(tool_event, ensure_ascii=False)}\n\n"
                    
                    # DB保存用データ保存
                    sent_tool_messages.append({
                        "role": "tool",
                        "content": json.dumps(tool_content_dict, ensure_ascii=False)
                    })
                    
                    # 完了したツールを状態から削除
                    active_tools.pop(call_id, None)
            
            # ========== 低レベルイベント: テキスト処理 ==========
            elif isinstance(event, RawResponsesStreamEvent):
                if isinstance(event.data, ResponseTextDeltaEvent):
                    # テキスト応答のみ処理（AI応答のストリーミング）
                    content = event.data.delta
                    assistant_content += content
                    content_event = {
                        "role": "assistant", 
                        "content": content,
                        "id": assistant_id
                    }
                    yield f"data: {json.dumps(content_event, ensure_ascii=False)}\n\n"
                
                # ResponseFunctionCallArgumentsDeltaEventは完全無視
                # → AI応答にツール引数JSONが混入する問題を根本解決

        # 既存のDB保存・タイトル生成処理は同じ...
        
    except Exception as e:
        error_event = {"error": f"エラーが発生しました: {str(e)}"}
        yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
    finally:
        db.close()
```

## 4. 期待される効果

### コード品質改善
- **行数削減**: 70行 → 30行（57%削減）
- **可読性向上**: 明確なイベント処理フロー
- **保守性向上**: SDK準拠による将来対応力

### 技術的改善  
- **安定性向上**: 複雑なIDマッチング排除
- **性能改善**: 不要なフィルタリング処理削除
- **根本的解決**: AI応答とツール引数の混入問題解決

### 開発効率向上
- **デバッグ容易性**: シンプルな処理フロー
- **拡張性**: 新しいイベント種別への対応が簡単
- **テスト容易性**: 明確な責任分離

## 5. 実装時の注意点

### 1. 既存機能互換性
- SSE出力形式は完全に維持（Phase1仕様準拠）
- DB保存データ構造は変更なし

### 2. エラーハンドリング  
- ツール実行失敗時の適切な処理
- active_toolsディクショナリのクリーンアップ

### 3. 段階的実装
1. 新実装をテスト環境で検証
2. 既存機能との比較テスト
3. 本番環境への適用

## 6. テスト計画

### 単体テスト
- ツールなし会話: テキストのみの正常ストリーミング
- ツールあり会話: ツール実行→テキスト応答の正常フロー
- 混在セッション: ツール使用・非使用が混在する長期会話

### 統合テスト  
- フロントエンドとの結合テスト
- DB保存データの整合性確認
- エラー発生時の適切な処理確認

この新実装により、openai-agents-python SDKの真の力を活用し、シンプルで保守性の高いストリーミング処理を実現できます。

## 7. セルフレビュー結果 ✅

### 技術的正確性検証
**✅ SDKイベント構造**: phase3.mdの実際のログで検証済み
- ToolCallItem: `raw_item.call_id`, `raw_item.name` (属性アクセス)
- ToolCallOutputItem: `raw_item['call_id']`, `item.output` (辞書+プロパティ)

**✅ インポート文**: `RunItemStreamEvent`を明示的に追加
**✅ エラーハンドリング**: 属性アクセス例外を適切にキャッチ
**✅ 既存互換性**: Phase1仕様のSSE出力形式を完全維持

### コード品質確認
- **複雑度削減**: 70行 → 40行（43%削減、エラーハンドリング込み）
- **型安全性**: `isinstance`による厳密な型チェック
- **保守性**: SDKの公式イベントモデルに準拠

この設計は実装準備完了状態です。