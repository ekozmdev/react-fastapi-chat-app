#!/usr/bin/env python3
"""
ユーザー管理スクリプト

使用方法:
    python scripts/manage_users.py list                          # ユーザー一覧表示
    python scripts/manage_users.py register                      # 対話形式でユーザー登録
    python scripts/manage_users.py activate user@example.com     # ユーザー有効化
    python scripts/manage_users.py deactivate user@example.com   # ユーザー無効化
    python scripts/manage_users.py delete user@example.com       # ユーザー削除
"""

import argparse
import getpass
import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import find_dotenv, load_dotenv
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.constants import MIN_PASSWORD_LENGTH
from app.models import User

# データベース接続
DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# パスワードハッシュ化（bcrypt使用）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# モデルをインポート


def get_password_hash(password: str) -> str:
    """パスワードをハッシュ化"""
    return pwd_context.hash(password)


def validate_email(email: str) -> bool:
    """メールアドレスの簡単な検証"""
    return "@" in email and "." in email.split("@")[1]


def validate_password(password: str) -> bool:
    """パスワード強度の検証"""
    if len(password) < MIN_PASSWORD_LENGTH:
        return False
    if not any(c.isalpha() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    return True


def list_users():
    """ユーザー一覧を表示"""
    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.created_at.desc()).all()

        if not users:
            print("登録されているユーザーはありません。")
            return

        print(
            f"{'ID':<36} {'メール':<30} {'ユーザー名':<20} {'ステータス':<10} {'作成日'}"
        )
        print("-" * 110)

        for user in users:
            status = "有効" if user.is_active else "無効"
            created_at = user.created_at.strftime("%Y-%m-%d %H:%M")
            print(
                f"{user.id:<36} {user.email:<30} {user.username:<20} {status:<10} {created_at}"
            )

    except Exception as e:
        print(f"エラー: {e}")
    finally:
        db.close()


def register_user():  # noqa: C901
    """対話形式でユーザーを登録"""
    db = SessionLocal()
    try:
        print("新規ユーザー登録")
        print("-" * 20)

        # メールアドレス入力
        while True:
            email = input("メールアドレス: ").strip()
            if not email:
                print("メールアドレスを入力してください。")
                continue
            if not validate_email(email):
                print("有効なメールアドレスを入力してください。")
                continue

            # 重複チェック
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                print("このメールアドレスは既に登録されています。")
                continue
            break

        # ユーザー名入力
        while True:
            username = input("ユーザー名: ").strip()
            if not username:
                print("ユーザー名を入力してください。")
                continue
            if len(username) < 2:
                print("ユーザー名は2文字以上で入力してください。")
                continue

            # 重複チェック
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                print("このユーザー名は既に使用されています。")
                continue
            break

        # パスワード入力
        while True:
            password = getpass.getpass("パスワード: ")
            if not password:
                print("パスワードを入力してください。")
                continue
            if not validate_password(password):
                print(f"パスワードは{MIN_PASSWORD_LENGTH}文字以上で、英字と数字を含む必要があります。")
                continue

            password_confirm = getpass.getpass("パスワード（確認）: ")
            if password != password_confirm:
                print("パスワードが一致しません。")
                continue
            break

        # ユーザー作成
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            username=username,
            password_hash=get_password_hash(password),
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        db.add(user)
        db.commit()

        print("\nユーザーが正常に登録されました:")
        print(f"  ID: {user.id}")
        print(f"  メール: {user.email}")
        print(f"  ユーザー名: {user.username}")

    except Exception as e:
        print(f"エラー: {e}")
        db.rollback()
    finally:
        db.close()


def activate_user(email: str):
    """ユーザーを有効化"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"ユーザーが見つかりません: {email}")
            return

        if user.is_active:
            print(f"ユーザーは既に有効です: {email}")
            return

        user.is_active = True
        user.updated_at = datetime.now(UTC)
        db.commit()

        print(f"ユーザーを有効化しました: {email}")

    except Exception as e:
        print(f"エラー: {e}")
        db.rollback()
    finally:
        db.close()


def deactivate_user(email: str):
    """ユーザーを無効化"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"ユーザーが見つかりません: {email}")
            return

        if not user.is_active:
            print(f"ユーザーは既に無効です: {email}")
            return

        user.is_active = False
        user.updated_at = datetime.now(UTC)
        db.commit()

        print(f"ユーザーを無効化しました: {email}")

    except Exception as e:
        print(f"エラー: {e}")
        db.rollback()
    finally:
        db.close()


def delete_user(email: str):
    """ユーザーを削除"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"ユーザーが見つかりません: {email}")
            return

        # 確認
        print(f"ユーザー '{user.username}' ({email}) を削除しようとしています。")
        print("このユーザーに関連する全ての会話とメッセージも削除されます。")
        confirm = input("本当に削除しますか？ (yes/no): ").strip().lower()

        if confirm not in ["yes", "y"]:
            print("削除をキャンセルしました。")
            return

        db.delete(user)
        db.commit()

        print(f"ユーザーを削除しました: {email}")

    except Exception as e:
        print(f"エラー: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="ユーザー管理スクリプト")
    subparsers = parser.add_subparsers(dest="command", help="利用可能なコマンド")

    # list コマンド
    subparsers.add_parser("list", help="ユーザー一覧を表示")

    # register コマンド
    subparsers.add_parser("register", help="対話形式でユーザーを登録")

    # activate コマンド
    activate_parser = subparsers.add_parser("activate", help="ユーザーを有効化")
    activate_parser.add_argument("email", help="ユーザーのメールアドレス")

    # deactivate コマンド
    deactivate_parser = subparsers.add_parser("deactivate", help="ユーザーを無効化")
    deactivate_parser.add_argument("email", help="ユーザーのメールアドレス")

    # delete コマンド
    delete_parser = subparsers.add_parser("delete", help="ユーザーを削除")
    delete_parser.add_argument("email", help="ユーザーのメールアドレス")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # コマンド実行
    if args.command == "list":
        list_users()
    elif args.command == "register":
        register_user()
    elif args.command == "activate":
        activate_user(args.email)
    elif args.command == "deactivate":
        deactivate_user(args.email)
    elif args.command == "delete":
        delete_user(args.email)


if __name__ == "__main__":
    main()
