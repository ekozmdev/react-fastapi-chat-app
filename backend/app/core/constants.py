"""アプリケーション定数定義"""

# OpenAI設定のデフォルト値
DEFAULT_OPENAI_MODEL = "gpt-4o"

# データベース設定のデフォルト値
DEFAULT_DATABASE_URL = "postgresql+psycopg://chatuser:chatpassword@localhost:5432/chatdb"

# JWT認証設定のデフォルト値
DEFAULT_JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24時間
