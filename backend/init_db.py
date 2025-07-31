#!/usr/bin/env python3
"""
データベース初期化スクリプト
初回セットアップ時にテーブルを作成します
"""

import os

from sqlalchemy import create_engine

from app.core.config import settings
from app.models import Base


def init_database():
    """データベースとテーブルを初期化"""
    database_url = settings.DATABASE_URL

    print(f"Connecting to database: {database_url}")
    engine = create_engine(database_url)

    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    print("Database initialization completed!")


if __name__ == "__main__":
    init_database()
