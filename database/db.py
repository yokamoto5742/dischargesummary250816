import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from utils.config import (
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER,
    POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_SSL,
    DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_TIMEOUT, DB_POOL_RECYCLE
)
from utils.exceptions import DatabaseError


class DatabaseManager:
    _instance = None
    _engine = None
    _session_factory = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DatabaseManager()
        return cls._instance

    def __init__(self):
        if DatabaseManager._engine is not None:
            return

        database_url = os.environ.get("DATABASE_URL")

        if database_url:
            try:
                if database_url.startswith("postgres://"):
                    database_url = database_url.replace("postgres://", "postgresql://", 1)

                if "?" in database_url:
                    database_url += "&sslmode=require"
                else:
                    database_url += "?sslmode=require"

                connection_string = database_url

            except Exception as e:
                raise DatabaseError(f"DATABASE_URLの解析に失敗しました: {str(e)}")
        else:
            if not all([POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
                raise DatabaseError(
                    "PostgreSQL接続情報が設定されていません。環境変数または設定ファイルを確認してください。")

            connection_string = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

            if POSTGRES_SSL:
                connection_string += f"?sslmode={POSTGRES_SSL}"

        try:
            DatabaseManager._engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_pre_ping=True,
                pool_size=DB_POOL_SIZE,
                max_overflow=DB_MAX_OVERFLOW,
                pool_timeout=DB_POOL_TIMEOUT,
                pool_recycle=DB_POOL_RECYCLE
            )

            DatabaseManager._session_factory = sessionmaker(bind=DatabaseManager._engine)

            with DatabaseManager._engine.connect() as conn:
                conn.execute(text("SELECT 1"))

        except Exception as e:
            raise DatabaseError(f"PostgreSQLへの接続に失敗しました: {str(e)}")

    @staticmethod
    def get_engine():
        return DatabaseManager._engine

    @staticmethod
    def get_session():
        if DatabaseManager._session_factory is None:
            raise DatabaseError("データベース接続が初期化されていません")
        return DatabaseManager._session_factory()

    def execute_query(self, query, params=None, fetch=True):
        session = self.get_session()
        try:
            result = session.execute(text(query), params or {})
            if fetch:
                data = []
                for row in result:
                    if hasattr(row, '_mapping'):
                        data.append(dict(row._mapping))
                session.commit()
                return data
            session.commit()
            return None
        except Exception as e:
            session.rollback()
            raise DatabaseError(f"クエリ実行中にエラーが発生しました: {str(e)}")
        finally:
            session.close()


def get_usage_collection():
    try:
        db_manager = DatabaseManager.get_instance()
        query = "SELECT * FROM summary_usage"
        return db_manager.execute_query(query)
    except Exception as e:
        raise DatabaseError(f"使用状況の取得に失敗しました: {str(e)}")


def get_settings_collection(app_type=None):
    try:
        db_manager = DatabaseManager.get_instance()
        if app_type:
            query = "SELECT * FROM app_settings WHERE app_type = :app_type"
            return db_manager.execute_query(query, {"app_type": app_type})
        else:
            query = "SELECT * FROM app_settings"
            return db_manager.execute_query(query)
    except Exception as e:
        raise DatabaseError(f"設定の取得に失敗しました: {str(e)}")
