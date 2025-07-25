"""
Enhanced streaming solution for early tool call detection
openai-agents-python SDKでのツール実行早期検出のための拡張ストリーミング機能
"""

import json
import time
from typing import Any, Dict, List, Optional, AsyncGenerator
from agents import Agent, Runner
from agents.stream_events import RunItemStreamEvent
import logging

logger = logging.getLogger(__name__)

class EnhancedToolStreamHandler:
    """ツール実行の早期検出と詳細管理を行うハンドラー"""
    
    def __init__(self):
        self.pending_tools: Dict[str, Dict[str, Any]] = {}
        self.completed_tools: List[Dict[str, Any]] = []
        self.tool_execution_callbacks = []
    
    def add_callback(self, callback):
        """ツール実行イベントのコールバックを追加"""
        self.tool_execution_callbacks.append(callback)
    
    async def _notify_tool_start(self, tool_name: str, tool_call_id: str, arguments: Dict[str, Any] = None):
        """ツール開始の通知"""
        for callback in self.tool_execution_callbacks:
            try:
                await callback("tool_start", {
                    "tool_name": tool_name,
                    "tool_call_id": tool_call_id,
                    "arguments": arguments or {},
                    "timestamp": time.time()
                })
            except Exception as e:
                logger.error(f"Tool start callback error: {e}")
    
    async def _notify_tool_complete(self, tool_call_id: str, output: str = None, error: str = None):
        """ツール完了の通知"""
        for callback in self.tool_execution_callbacks:
            try:
                await callback("tool_complete", {
                    "tool_call_id": tool_call_id,
                    "output": output,
                    "error": error,
                    "timestamp": time.time()
                })
            except Exception as e:
                logger.error(f"Tool complete callback error: {e}")
    
    async def enhanced_stream_events(self, agent: Agent, messages: List[Dict[str, Any]]) -> AsyncGenerator[Any, None]:
        """拡張されたストリーミングイベント処理"""
        
        # 標準のストリーミング実行
        result = Runner.run_streamed(agent, messages)
        
        async for event in result.stream_events():
            # デバッグ用の詳細情報出力
            logger.info(f"Event received: type={event.type}")
            
            # 既存のイベント処理を継続
            yield event
            
            # raw_response_eventでの早期検出を強化
            if event.type == "raw_response_event":
                await self._handle_raw_response_event(event)
            
            # RunItemStreamEventでの確実な検出
            elif isinstance(event, RunItemStreamEvent):
                await self._handle_run_item_stream_event(event)
    
    async def _handle_raw_response_event(self, event):
        """raw_response_eventの詳細処理"""
        try:
            # イベントの構造を詳細に調査
            if hasattr(event, "data") and event.data is not None:
                # 複数のパターンでツールコールを検出
                tool_calls = self._extract_tool_calls_from_raw_event(event)
                
                for tool_call in tool_calls:
                    tool_name = tool_call.get('name')
                    tool_call_id = tool_call.get('id', f"{tool_name}_{int(time.time() * 1000)}")
                    arguments = tool_call.get('arguments', {})
                    
                    if tool_call_id not in self.pending_tools:
                        self.pending_tools[tool_call_id] = {
                            'name': tool_name,
                            'id': tool_call_id,
                            'arguments': arguments,
                            'start_time': time.time(),
                            'detected_early': True
                        }
                        
                        # 早期検出の通知
                        await self._notify_tool_start(tool_name, tool_call_id, arguments)
                        logger.info(f"Early tool detection: {tool_name} ({tool_call_id})")
        
        except Exception as e:
            logger.error(f"Raw event handling error: {e}")
    
    async def _handle_run_item_stream_event(self, event):
        """RunItemStreamEventの処理"""
        try:
            if event.item.type == "tool_call_item":
                # ツール実行の開始または更新
                raw_item = event.item.raw_item
                tool_name = getattr(raw_item, 'name', 'unknown')
                tool_call_id = getattr(raw_item, 'call_id', f"{tool_name}_{int(time.time() * 1000)}")
                
                if tool_call_id not in self.pending_tools:
                    # 早期検出されていない場合の後発検出
                    arguments_json = getattr(raw_item, 'arguments', '{}')
                    try:
                        arguments = json.loads(arguments_json) if arguments_json else {}
                    except (json.JSONDecodeError, ValueError):
                        arguments = {}
                    
                    self.pending_tools[tool_call_id] = {
                        'name': tool_name,
                        'id': tool_call_id,
                        'arguments': arguments,
                        'start_time': time.time(),
                        'detected_early': False
                    }
                    
                    await self._notify_tool_start(tool_name, tool_call_id, arguments)
                    logger.info(f"Late tool detection: {tool_name} ({tool_call_id})")
            
            elif event.item.type == "tool_call_output_item":
                # ツール実行の完了
                raw_item = event.item.raw_item
                tool_call_id = raw_item.get('call_id', 'unknown') if isinstance(raw_item, dict) else getattr(raw_item, 'call_id', 'unknown')
                tool_output = getattr(event.item, 'output', '')
                
                if tool_call_id in self.pending_tools:
                    tool_info = self.pending_tools[tool_call_id]
                    execution_time = time.time() - tool_info['start_time']
                    
                    completed_tool = {
                        **tool_info,
                        'output': tool_output,
                        'execution_time': execution_time,
                        'completed_at': time.time()
                    }
                    
                    self.completed_tools.append(completed_tool)
                    del self.pending_tools[tool_call_id]
                    
                    await self._notify_tool_complete(tool_call_id, tool_output)
                    logger.info(f"Tool completed: {tool_info['name']} ({execution_time:.2f}s)")
        
        except Exception as e:
            logger.error(f"Run item event handling error: {e}")
    
    def _extract_tool_calls_from_raw_event(self, event) -> List[Dict[str, Any]]:
        """raw_response_eventからツールコールを抽出"""
        tool_calls = []
        
        try:
            data = event.data
            
            # パターン1: delta.tool_calls
            if hasattr(data, 'delta') and data.delta and hasattr(data.delta, 'tool_calls'):
                for tool_call in data.delta.tool_calls:
                    if hasattr(tool_call, 'function') and hasattr(tool_call.function, 'name'):
                        tool_calls.append({
                            'name': tool_call.function.name,
                            'id': getattr(tool_call, 'id', None),
                            'arguments': getattr(tool_call.function, 'arguments', {})
                        })
            
            # パターン2: direct tool_calls
            if hasattr(data, 'tool_calls') and data.tool_calls:
                for tool_call in data.tool_calls:
                    if hasattr(tool_call, 'function') and hasattr(tool_call.function, 'name'):
                        tool_calls.append({
                            'name': tool_call.function.name,
                            'id': getattr(tool_call, 'id', None),
                            'arguments': getattr(tool_call.function, 'arguments', {})
                        })
            
            # パターン3: JSON content parsing
            if hasattr(data, 'content') and isinstance(data.content, str):
                try:
                    content_data = json.loads(data.content)
                    if 'tool_calls' in content_data:
                        for tool_call in content_data['tool_calls']:
                            if 'function' in tool_call and 'name' in tool_call['function']:
                                tool_calls.append({
                                    'name': tool_call['function']['name'],
                                    'id': tool_call.get('id'),
                                    'arguments': tool_call['function'].get('arguments', {})
                                })
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass
        
        except Exception as e:
            logger.error(f"Tool call extraction error: {e}")
        
        return tool_calls
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """実行サマリーを取得"""
        return {
            'pending_tools': list(self.pending_tools.values()),
            'completed_tools': self.completed_tools,
            'total_tools': len(self.completed_tools) + len(self.pending_tools),
            'success_count': len([t for t in self.completed_tools if 'output' in t and not t.get('error')]),
            'error_count': len([t for t in self.completed_tools if t.get('error')])
        }

# 使用例とヘルパー関数
async def create_enhanced_sse_stream(agent: Agent, messages: List[Dict[str, Any]], tool_callback=None):
    """拡張SSEストリームの作成"""
    handler = EnhancedToolStreamHandler()
    
    if tool_callback:
        handler.add_callback(tool_callback)
    
    async for event in handler.enhanced_stream_events(agent, messages):
        yield event