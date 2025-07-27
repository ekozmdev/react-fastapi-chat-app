"""アプリケーション設定管理"""

import os
from typing import Any

from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()


class Settings:
    """アプリケーション設定クラス"""
    
    # アプリケーション基本設定
    APP_TITLE: str = "LLM Chat API"
    APP_VERSION: str = "0.2.0"
    
    # OpenAI設定
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # データベース設定
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # CORS設定
    CORS_ORIGINS: list[str] = ["*"]  # 本番環境では適切に制限する
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]
    


# グローバル設定インスタンス
settings = Settings()