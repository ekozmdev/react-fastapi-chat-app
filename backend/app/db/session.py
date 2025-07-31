"""データベースセッション管理"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..core.config import settings

# データベースURL取得（設定から取得、デフォルト値はconstants.pyで管理）
DATABASE_URL = settings.DATABASE_URL

# SQLAlchemyエンジンとセッション設定
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """データベースセッションを取得"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
