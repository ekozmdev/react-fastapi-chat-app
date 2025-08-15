"""外部APIクライアント管理モジュール"""

from contextlib import asynccontextmanager

from agents import Agent, ModelSettings
from fastapi import FastAPI
from openai import AsyncOpenAI

from .core.config import settings
from .tools import AVAILABLE_TOOLS


class APIClients:
    """外部APIクライアント管理クラス"""

    def __init__(self):
        self.openai_client: AsyncOpenAI | None = None
        self.chat_agent: Agent | None = None

    async def initialize(self):
        """クライアント初期化"""
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        self.chat_agent = Agent(
            name="ChatAssistant",
            instructions="""あなたは親切で知識豊富なアシスタントです。
            ユーザーの質問に正確かつ丁寧に答えてください。
            必要に応じてツールを使用してください。
            時刻の取得や計算が必要な場合は、適切なツールを使用してください。
            回答は常にユーザーの言語で行ってください。
            Markdownで箇条書きを出力するときはtight list形式で出力してください。
            箇条書き・説明の順で列挙する場合は列挙する場合も要素の間に改行を入れないでください。
            loose list形式で出力すると、あなたの回答のレイアウトが崩れます。
            """,
            model=settings.OPENAI_MODEL,
            model_settings=ModelSettings(
                max_tokens=settings.OPENAI_MAX_TOKENS,
                temperature=settings.OPENAI_TEMPERATURE,
            ),
            tools=AVAILABLE_TOOLS,
        )

    async def close(self):
        """リソースクリーンアップ"""
        if self.openai_client:
            await self.openai_client.close()


_clients_instance: APIClients | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    global _clients_instance
    _clients_instance = APIClients()
    await _clients_instance.initialize()
    yield
    if _clients_instance:
        await _clients_instance.close()


# Dependency functions
def get_openai_client() -> AsyncOpenAI:
    """OpenAI クライアント取得依存性"""
    if _clients_instance is None or _clients_instance.openai_client is None:
        raise RuntimeError("OpenAI client not initialized")
    return _clients_instance.openai_client


def get_chat_agent() -> Agent:
    """Chat Agent 取得依存性"""
    if _clients_instance is None or _clients_instance.chat_agent is None:
        raise RuntimeError("Chat agent not initialized")
    return _clients_instance.chat_agent
