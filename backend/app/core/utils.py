"""共通ユーティリティ関数"""

import uuid


def generate_unique_id() -> str:
    """
    一意IDを生成する

    現在はUUIDを返すが、将来的に数字IDなど別形式に変更可能
    """
    return str(uuid.uuid4())
