"""
ツール機能実装
基本的なツール関数の定義と管理
"""

from datetime import UTC, datetime

from agents import function_tool


@function_tool
def get_current_time() -> str:
    """現在の時刻を取得します。"""
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

        # 安全な数式評価（文字チェック済みのためevalを使用）
        result = eval(expression)  # noqa: S307
        return f"{expression} = {result}"
    except Exception as e:
        return f"計算エラー: {str(e)}"


@function_tool
def web_search(query: str, max_results: int = 5) -> str:
    """Web検索を実行します（Mock版）。

    Args:
        query: 検索クエリ
        max_results: 最大結果数（デフォルト: 5）

    Returns:
        検索結果（マークダウン形式）
    """
    search_results = [
        {
            "title": f"{query}に関するサンプル記事1",
            "url": f"https://example.com/search/{query.replace(' ', '-')}/1",
            "description": f"{query}について詳しく解説したサンプル記事です。専門的な内容を含んでいます。",
        },
        {
            "title": f"{query} - Wikipedia風記事",
            "url": f"https://example.com/wiki/{query.replace(' ', '_')}",
            "description": f"{query}の基本的な情報と背景について包括的に説明している百科事典風の記事です。",
        },
        {
            "title": f"{query}のベストプラクティス",
            "url": f"https://example.com/blog/{query.replace(' ', '-')}-best-practices",
            "description": f"{query}に関するベストプラクティスやTipsをまとめたブログ記事です。",
        },
        {
            "title": f"{query}入門ガイド",
            "url": f"https://example.com/guide/{query.replace(' ', '-')}-guide",
            "description": f"{query}の初心者向け入門ガイドです。基本から応用まで幅広くカバーしています。",
        },
        {
            "title": f"{query}の最新動向",
            "url": f"https://example.com/news/{query.replace(' ', '-')}-2025",
            "description": f"2025年における{query}の最新動向やトレンドについて報告している記事です。",
        },
    ]

    limited_results = search_results[:max_results]

    markdown_output = f"# 検索結果: {query}\n\n"
    markdown_output += (
        f"検索クエリ「**{query}**」に対する結果 ({len(limited_results)}件):\n\n"
    )

    for i, result in enumerate(limited_results, 1):
        markdown_output += f"## {i}. {result['title']}\n"
        markdown_output += f"🔗 **URL**: {result['url']}\n\n"
        markdown_output += f"📝 **概要**: {result['description']}\n\n"
        markdown_output += "---\n\n"

    markdown_output += "*注: これはMock検索結果です。実際のWeb検索ではありません。*"

    return markdown_output


# 利用可能なツールリスト
AVAILABLE_TOOLS = [
    get_current_time,
    calculate,
    web_search,
]
