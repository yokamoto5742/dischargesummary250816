import os
from typing import Dict, List, Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from utils.config import (
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER,
    POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_SSL,
    DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_TIMEOUT, DB_POOL_RECYCLE
)
from utils.exceptions import DatabaseError


class QueryBuilder:

    @staticmethod
    def build_select_query(table: str,
                           columns: List[str] = None,
                           where_conditions: List[str] = None,
                           group_by: List[str] = None,
                           order_by: List[str] = None) -> str:
        columns_str = ", ".join(columns) if columns else "*"
        query = f"SELECT {columns_str} FROM {table}"

        if where_conditions:
            query += f" WHERE {' AND '.join(where_conditions)}"

        if group_by:
            query += f" GROUP BY {', '.join(group_by)}"

        if order_by:
            query += f" ORDER BY {', '.join(order_by)}"

        return query

    @staticmethod
    def build_upsert_query(table: str,
                           columns: List[str],
                           conflict_columns: List[str],
                           update_columns: List[str] = None) -> str:
        placeholders = [f":{col}" for col in columns]

        query = f"""
        INSERT INTO {table} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        ON CONFLICT ({', '.join(conflict_columns)})
        DO UPDATE SET
        """

        if update_columns:
            updates = [f"{col} = EXCLUDED.{col}" for col in update_columns]
        else:
            updates = [f"{col} = EXCLUDED.{col}" for col in columns if col not in conflict_columns]

        query += ", ".join(updates)
        return query

    @staticmethod
    def build_delete_query(table: str, where_conditions: List[str]) -> str:
        return f"DELETE FROM {table} WHERE {' AND '.join(where_conditions)}"


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

    def select_with_conditions(self, table: str,
                               conditions: Dict[str, Any] = None,
                               columns: List[str] = None,
                               order_by: List[str] = None) -> List[Dict[str, Any]]:
        where_conditions = []
        params = {}

        if conditions:
            for key, value in conditions.items():
                if value is not None:
                    where_conditions.append(f"{key} = :{key}")
                    params[key] = value
                else:
                    where_conditions.append(f"{key} IS NULL")

        query = QueryBuilder.build_select_query(
            table=table,
            columns=columns,
            where_conditions=where_conditions,
            order_by=order_by
        )

        return self.execute_query(query, params)

    def upsert_record(self, table: str,
                      data: Dict[str, Any],
                      conflict_columns: List[str]) -> bool:
        columns = list(data.keys())
        query = QueryBuilder.build_upsert_query(
            table=table,
            columns=columns,
            conflict_columns=conflict_columns
        )

        try:
            self.execute_query(query, data, fetch=False)
            return True
        except Exception as e:
            raise DatabaseError(f"レコードの作成/更新に失敗しました: {str(e)}")

    def delete_with_conditions(self, table: str,
                               conditions: Dict[str, Any]) -> int:
        where_conditions = []
        params = {}

        for key, value in conditions.items():
            if value is not None:
                where_conditions.append(f"{key} = :{key}")
                params[key] = value
            else:
                where_conditions.append(f"{key} IS NULL")

        query = QueryBuilder.build_delete_query(
            table=table,
            where_conditions=where_conditions
        )

        session = self.get_session()
        try:
            result = session.execute(text(query), params)
            deleted_count = result.rowcount
            session.commit()
            return deleted_count
        except Exception as e:
            session.rollback()
            raise DatabaseError(f"レコードの削除に失敗しました: {str(e)}")
        finally:
            session.close()


def get_usage_collection():
    try:
        db_manager = DatabaseManager.get_instance()
        return db_manager.select_with_conditions("summary_usage")
    except Exception as e:
        raise DatabaseError(f"使用状況の取得に失敗しました: {str(e)}")


def get_settings_collection(app_type=None):
    try:
        db_manager = DatabaseManager.get_instance()
        conditions = {"app_type": app_type} if app_type else None
        return db_manager.select_with_conditions("app_settings", conditions)
    except Exception as e:
        raise DatabaseError(f"設定の取得に失敗しました: {str(e)}")
