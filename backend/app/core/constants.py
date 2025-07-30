"""アプリケーション定数定義"""

# OpenAI設定のデフォルト値
DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFAULT_OPENAI_MAX_TOKENS = 1024
DEFAULT_OPENAI_TEMPERATURE = 0.7

# データベース設定のデフォルト値
DEFAULT_DATABASE_URL = "postgresql+psycopg://chatuser:chatpassword@localhost:5432/chatdb"

# JWT認証設定のデフォルト値
DEFAULT_JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24時間
