"""
Phase 2: データベース連携型ツール実行管理
Phase 1のStreamToolTrackerを拡張したデータベース連携型管理システム
"""

import logging
import time
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from .models import ToolExecution

# Phase 1で学んだ：適切なログ設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DatabaseToolManager:
    """Phase 2: データベース連携型ツール実行管理"""

    def __init__(self, db: Session, message_id: str):
        self.db = db
        self.message_id = message_id
        self.execution_order = 0

        # Phase 1互換性のため保持
        self.tools_used: list[dict[str, Any]] = []
        self.current_tool: dict[str, Any] | None = None

    def record_tool_call(
        self, tool_call_id: str, tool_name: str, arguments: dict[str, Any]
    ) -> str:
        """ツール呼び出しの記録（Phase 2の新機能）"""
        try:
            self.execution_order += 1

            # Phase 1で学んだ：安全なattribute取得
            safe_arguments = arguments if isinstance(arguments, dict) else {}

            # Phase 2: データベースに詳細記録
            tool_execution = ToolExecution(
                message_id=self.message_id,
                execution_order=self.execution_order,
                tool_call_id=tool_call_id,
                tool_name=tool_name,
                tool_arguments=safe_arguments,
                call_status="called",
                called_at=datetime.now(UTC),
            )

            self.db.add(tool_execution)
            self.db.commit()

            # Phase 1互換性の維持
            self.current_tool = {
                "name": tool_name,
                "input": safe_arguments,
                "start_time": time.time() * 1000,
                "status": "called",
                "execution_id": tool_execution.id,
            }

            logger.info(
                f"Tool call recorded: {tool_name} (order: {self.execution_order})"
            )
            return tool_execution.id

        except Exception as e:
            logger.error(f"Tool call recording failed: {e}")
            return None

    def start_execution(self, tool_call_id: str) -> bool:
        """ツール実行開始"""
        try:
            execution = self._get_execution_by_call_id(tool_call_id)
            if execution:
                execution.call_status = "executing"
                execution.started_at = datetime.now(UTC)
                self.db.commit()

                # Phase 1互換性の更新
                if (
                    self.current_tool
                    and self.current_tool.get("execution_id") == execution.id
                ):
                    self.current_tool["status"] = "executing"

                logger.info(f"Tool execution started: {execution.tool_name}")
                return True

        except Exception as e:
            logger.error(f"Tool execution start failed: {e}")

        return False

    def complete_execution(
        self, tool_call_id: str, output: str = None, error: str = None
    ) -> bool:
        """ツール実行完了"""
        try:
            execution = self._get_execution_by_call_id(tool_call_id)
            if execution:
                # 実行時間の計算
                if execution.started_at:
                    execution_time = int(
                        (datetime.now(UTC) - execution.started_at).total_seconds()
                        * 1000
                    )
                else:
                    execution_time = int(
                        (datetime.now(UTC) - execution.called_at).total_seconds() * 1000
                    )

                # 結果の記録
                execution.call_status = "completed"
                execution.execution_status = "success" if not error else "error"
                execution.tool_output = output
                execution.error_message = error
                execution.completed_at = datetime.now(UTC)
                execution.execution_time_ms = execution_time

                self.db.commit()

                # Phase 1互換性：tools_usedリストに追加
                self.tools_used.append(
                    {
                        "name": execution.tool_name,
                        "input": execution.tool_arguments,
                        "output": output,
                        "error": error,
                        "status": "success" if not error else "error",
                        "execution_time_ms": execution_time,
                    }
                )

                logger.info(
                    f"Tool execution completed: {execution.tool_name} ({execution_time}ms)"
                )
                return True

        except Exception as e:
            logger.error(f"Tool execution completion failed: {e}")

        return False

    def get_metadata(self) -> dict[str, Any] | None:
        """Phase 1互換性：tool_metadataを生成"""
        if not self.tools_used:
            return None

        success_count = sum(1 for t in self.tools_used if t["status"] == "success")
        error_count = len(self.tools_used) - success_count
        total_time = sum(t["execution_time_ms"] for t in self.tools_used)

        return {
            "tools_used": self.tools_used,
            "summary": {
                "total_tools": len(self.tools_used),
                "total_time_ms": total_time,
                "success_count": success_count,
                "error_count": error_count,
            },
        }

    def _get_execution_by_call_id(self, tool_call_id: str) -> ToolExecution | None:
        """ツールコールIDから実行記録を取得"""
        try:
            return (
                self.db.query(ToolExecution)
                .filter(
                    ToolExecution.message_id == self.message_id,
                    ToolExecution.tool_call_id == tool_call_id,
                )
                .first()
            )
        except Exception as e:
            logger.error(f"Failed to get execution by call_id: {e}")
            return None

    def get_all_executions(self) -> list[ToolExecution]:
        """メッセージの全ツール実行記録を取得"""
        try:
            return (
                self.db.query(ToolExecution)
                .filter(ToolExecution.message_id == self.message_id)
                .order_by(ToolExecution.execution_order)
                .all()
            )
        except Exception as e:
            logger.error(f"Failed to get all executions: {e}")
            return []
