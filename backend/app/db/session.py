"""データベースセッション管理"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..core.config import settings

# データベースURL取得（設定から、またはデフォルト値）
DATABASE_URL = (
    settings.DATABASE_URL 
    if settings.DATABASE_URL 
    else "postgresql+psycopg://chatuser:chatpassword@localhost:5432/chatdb"
)

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