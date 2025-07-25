"""
Phase 2: ツール実行の詳細追跡モデル
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from .base import Base


class ToolExecution(Base):
    """ツール実行の完全な記録（Phase 2）"""
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
    called_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    started_at = Column(DateTime, nullable=True)        # 実行開始時刻
    completed_at = Column(DateTime, nullable=True)      # 実行完了時刻
    execution_time_ms = Column(Integer, nullable=True)  # 実行時間(ミリ秒)
    
    # メタデータ
    agent_reasoning = Column(Text, nullable=True)       # なぜこのツールを呼び出したか
    
    # リレーション
    message = relationship("Message", back_populates="tool_executions")
    
    def __repr__(self):
        return f"<ToolExecution(id={self.id}, tool_name={self.tool_name}, status={self.call_status})>"