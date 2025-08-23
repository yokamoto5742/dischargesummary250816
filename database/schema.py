import time
from sqlalchemy import create_engine

from database.models import Base
from database.db import DatabaseManager
from utils.exceptions import DatabaseError


def create_tables():
    """ORMを使用してテーブルを作成"""
    try:
        db_manager = DatabaseManager.get_instance()
        engine = db_manager.get_engine()

        # ORMモデルからすべてのテーブルを作成
        Base.metadata.create_all(engine)

        return True
    except Exception as e:
        raise DatabaseError(f"テーブル作成中にエラーが発生しました: {str(e)}")


def drop_tables():
    """すべてのテーブルを削除（開発・テスト用）"""
    try:
        db_manager = DatabaseManager.get_instance()
        engine = db_manager.get_engine()

        Base.metadata.drop_all(engine)

        return True
    except Exception as e:
        raise DatabaseError(f"テーブル削除中にエラーが発生しました: {str(e)}")


def recreate_tables():
    """テーブルを再作成（開発・テスト用）"""
    try:
        drop_tables()
        create_tables()
        return True
    except Exception as e:
        raise DatabaseError(f"テーブル再作成中にエラーが発生しました: {str(e)}")


def initialize_database():
    """データベース初期化（リトライ機能付き）"""
    max_retries = 5
    retry_count = 0
    last_error = None

    while retry_count < max_retries:
        try:
            create_tables()
            return True
        except Exception as e:
            last_error = e
            retry_count += 1
            wait_time = 2 ** retry_count  # 指数バックオフ
            print(f"データベース初期化に失敗しました（試行 {retry_count}/{max_retries}）: {str(e)}")
            print(f"{wait_time}秒後に再試行します...")
            time.sleep(wait_time)

    raise DatabaseError(f"データベースの初期化に失敗しました: {str(last_error)}")


def check_tables_exist():
    """テーブルの存在確認"""
    try:
        db_manager = DatabaseManager.get_instance()
        engine = db_manager.get_engine()

        # メタデータを使用してテーブルの存在を確認
        Base.metadata.reflect(engine)

        expected_tables = {'app_settings', 'prompts', 'summary_usage'}
        existing_tables = set(Base.metadata.tables.keys())

        missing_tables = expected_tables - existing_tables

        if missing_tables:
            print(f"不足しているテーブル: {missing_tables}")
            return False

        print("すべてのテーブルが存在します")
        return True

    except Exception as e:
        raise DatabaseError(f"テーブル存在確認中にエラーが発生しました: {str(e)}")


def get_table_info():
    """テーブル情報を取得"""
    try:
        db_manager = DatabaseManager.get_instance()
        engine = db_manager.get_engine()

        Base.metadata.reflect(engine)

        table_info = {}
        for table_name, table in Base.metadata.tables.items():
            columns = []
            for column in table.columns:
                columns.append({
                    'name': column.name,
                    'type': str(column.type),
                    'nullable': column.nullable,
                    'primary_key': column.primary_key,
                    'default': str(column.default) if column.default else None
                })
            table_info[table_name] = {
                'columns': columns,
                'constraints': [str(constraint) for constraint in table.constraints]
            }

        return table_info

    except Exception as e:
        raise DatabaseError(f"テーブル情報取得中にエラーが発生しました: {str(e)}")


if __name__ == "__main__":
    """スクリプト直接実行時のテスト"""
    try:
        print("データベース初期化を開始します...")
        initialize_database()
        print("データベース初期化が完了しました")

        print("テーブル存在確認を実行します...")
        if check_tables_exist():
            print("すべてのテーブルが正常に作成されています")

        print("テーブル情報を取得します...")
        table_info = get_table_info()
        for table_name, info in table_info.items():
            print(f"\n--- {table_name} ---")
            print(f"カラム数: {len(info['columns'])}")
            for col in info['columns']:
                print(f"  {col['name']}: {col['type']} (nullable: {col['nullable']})")

    except DatabaseError as e:
        print(f"エラー: {e}")
    except Exception as e:
        print(f"予期しないエラー: {e}")
