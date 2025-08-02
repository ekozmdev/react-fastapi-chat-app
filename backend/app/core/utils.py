"""共通ユーティリティ関数"""

import uuid


def generate_uuid() -> str:
    """
    UUID4を生成して文字列として返す

    アプリケーション全体でUUID生成を統一するための共通関数
    """
    return str(uuid.uuid4())
