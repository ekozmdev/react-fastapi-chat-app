#!/usr/bin/env python3
"""
データベース初期化スクリプト
初回セットアップ時にテーブルを作成します
"""

import os

from dotenv import load_dotenv
from main import Base
from sqlalchemy import create_engine

load_dotenv()


def init_database():
    """データベースとテーブルを初期化"""
    database_url = os.getenv(
        "DATABASE_URL", "postgresql://chatuser:chatpassword@localhost:5432/chatdb"
    )

    print(f"Connecting to database: {database_url}")
    engine = create_engine(database_url)

    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    print("Database initialization completed!")


if __name__ == "__main__":
    init_database()
