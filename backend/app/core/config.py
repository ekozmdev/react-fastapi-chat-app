"""アプリケーション設定管理"""

import logging
import os

from dotenv import find_dotenv, load_dotenv

from .constants import (
    DEFAULT_DATABASE_URL,
    DEFAULT_JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    DEFAULT_OPENAI_MODEL,
)

# 環境変数を読み込み（プロジェクトルートの.envを自動検出）
dotenv_path = find_dotenv()
print(f"[CONFIG] Loading .env from: {dotenv_path}")
load_dotenv(dotenv_path)


def validate_required_env(key: str) -> str:
    """必須環境変数を検証・取得（未設定時はValueErrorを発生）"""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"{key} environment variable is required")
    return value


def validate_optional_env(key: str, default: str) -> str:
    """オプション環境変数を検証・取得（未設定時はデフォルト値を使用、デフォルト値使用時はワーニング出力）"""
    value = os.getenv(key)
    if not value:
        logging.warning(f"[CONFIG] {key} is using default value. Consider setting a custom value for production.")
        return default
    return value


class Settings:
    """アプリケーション設定クラス"""

    # アプリケーション基本設定
    APP_TITLE: str = "LLM Chat API"
    APP_VERSION: str = "0.2.0"

    # OpenAI設定
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

    # データベース設定
    DATABASE_URL: str = validate_optional_env("DATABASE_URL", DEFAULT_DATABASE_URL)

    # JWT認証設定
    JWT_SECRET_KEY: str = validate_required_env("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(validate_optional_env("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", str(DEFAULT_JWT_ACCESS_TOKEN_EXPIRE_MINUTES)))

    # CORS設定
    CORS_ORIGINS: list[str] = ["*"]  # 本番環境では適切に制限する
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]


# グローバル設定インスタンス
settings = Settings()
