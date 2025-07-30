"""アプリケーション定数定義"""

# OpenAI設定のデフォルト値
DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFAULT_OPENAI_MAX_TOKENS = 1024
DEFAULT_OPENAI_TEMPERATURE = 0.7

# データベース設定のデフォルト値
DEFAULT_DATABASE_URL = "postgresql+psycopg://chatuser:chatpassword@localhost:5432/chatdb"

# JWT認証設定のデフォルト値
DEFAULT_JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24時間

# CORS設定のデフォルト値
DEFAULT_CORS_ORIGINS = "http://localhost:3000,http://localhost:80"  # カンマ区切り文字列
DEFAULT_CORS_ALLOW_CREDENTIALS = "true"
DEFAULT_CORS_ALLOW_METHODS = "GET,POST,PUT,DELETE"  # カンマ区切り文字列

# アプリケーション設定のデフォルト値
DEFAULT_APP_TITLE = "LLM Chat API"

# セキュリティ設定のデフォルト値
MIN_PASSWORD_LENGTH = 8  # パスワード最小文字数
