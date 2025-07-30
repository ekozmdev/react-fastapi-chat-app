"""アプリケーション設定管理"""

import logging
import os

from dotenv import find_dotenv, load_dotenv

from .constants import (
    DEFAULT_CORS_ALLOW_CREDENTIALS,
    DEFAULT_CORS_ALLOW_METHODS,
    DEFAULT_CORS_ORIGINS,
    DEFAULT_DATABASE_URL,
    DEFAULT_JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    DEFAULT_OPENAI_MAX_TOKENS,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_OPENAI_TEMPERATURE,
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


def parse_comma_separated_list(value: str) -> list[str]:
    """カンマ区切り文字列をリストに変換（空白も除去）"""
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_bool(value: str) -> bool:
    """文字列をboolに変換"""
    return value.lower() in ("true", "1", "yes", "on")


class Settings:
    """アプリケーション設定クラス"""

    # アプリケーション基本設定
    APP_TITLE: str = "LLM Chat API"
    APP_VERSION: str = "0.2.0"

    # OpenAI設定
    OPENAI_API_KEY: str = validate_required_env("OPENAI_API_KEY")
    OPENAI_MODEL: str = validate_optional_env("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    OPENAI_MAX_TOKENS: int = int(validate_optional_env("OPENAI_MAX_TOKENS", str(DEFAULT_OPENAI_MAX_TOKENS)))
    OPENAI_TEMPERATURE: float = float(validate_optional_env("OPENAI_TEMPERATURE", str(DEFAULT_OPENAI_TEMPERATURE)))

    # データベース設定
    DATABASE_URL: str = validate_optional_env("DATABASE_URL", DEFAULT_DATABASE_URL)

    # JWT認証設定
    JWT_SECRET_KEY: str = validate_required_env("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(validate_optional_env("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", str(DEFAULT_JWT_ACCESS_TOKEN_EXPIRE_MINUTES)))

    # CORS設定
    CORS_ORIGINS: list[str] = parse_comma_separated_list(validate_optional_env("CORS_ORIGINS", DEFAULT_CORS_ORIGINS))
    CORS_ALLOW_CREDENTIALS: bool = parse_bool(validate_optional_env("CORS_ALLOW_CREDENTIALS", DEFAULT_CORS_ALLOW_CREDENTIALS))
    CORS_ALLOW_METHODS: list[str] = parse_comma_separated_list(validate_optional_env("CORS_ALLOW_METHODS", DEFAULT_CORS_ALLOW_METHODS))
    CORS_ALLOW_HEADERS: list[str] = ["*"]  # ヘッダーは現状維持


# グローバル設定インスタンス
settings = Settings()
