"""
Phase 1: ツール機能実装
基本的なツール関数の定義と管理
"""

import time
from datetime import UTC, datetime

from agents import function_tool


@function_tool
def get_current_time() -> str:
    """現在の時刻を取得します。"""
    # デバッグ用：長時間実行をシミュレート
    print("Tool execution starting... waiting 5 seconds")
    time.sleep(5)
    print("Tool execution completed!")
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
        # 安全な文字のみチェック
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return "エラー: 許可されていない文字が含まれています"

        # 安全な数式評価（evalを使用するが文字チェック済み）
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"計算エラー: {str(e)}"


# ==========================================
# ツール拡張ガイド
# ==========================================
# 新しいツールを追加する場合:
# 1. @function_tool デコレータを使って関数を定義
# 2. 下記のAVAILABLE_TOOLSリストに関数を追加
# 3. main.pyでの変更は不要（自動で反映されます）
# ==========================================

# 利用可能なツールリスト（新しいツールはここに追加）
AVAILABLE_TOOLS = [
    get_current_time,  # 現在時刻を取得
    calculate,  # 数式計算
    # 新しいツールはここに追加してください
    # 例: weather_tool, search_tool, etc.
]

# ツール追加例（コメントアウト）
# @function_tool
# def example_tool(param: str) -> str:
#     """新しいツールの例"""
#     return f"処理結果: {param}"
#
# 上記を定義したら AVAILABLE_TOOLS に example_tool を追加
