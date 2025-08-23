import os
from typing import Dict, List, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

from database.models import Base
from database.repositories import PromptRepository, UsageStatisticsRepository, SettingsRepository
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
    _scoped_session = None

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
            DatabaseManager._scoped_session = scoped_session(DatabaseManager._session_factory)

            # テーブル作成
            Base.metadata.create_all(DatabaseManager._engine)

        except Exception as e:
            raise DatabaseError(f"PostgreSQLへの接続に失敗しました: {str(e)}")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DatabaseManager()
        return cls._instance

    @staticmethod
    def get_engine():
        return DatabaseManager._engine

    @staticmethod
    def get_session_factory():
        return DatabaseManager._session_factory

    @staticmethod
    def get_scoped_session():
        return DatabaseManager._scoped_session

    # リポジトリのファクトリメソッド
    def get_prompt_repository(self) -> PromptRepository:
        """プロンプトリポジトリを取得"""
        return PromptRepository(self.get_session_factory())

    def get_usage_statistics_repository(self) -> UsageStatisticsRepository:
        """使用統計リポジトリを取得"""
        return UsageStatisticsRepository(self.get_session_factory())

    def get_settings_repository(self) -> SettingsRepository:
        """設定リポジトリを取得"""
        return SettingsRepository(self.get_session_factory())


# 後方互換性のための関数
def get_usage_collection():
    """使用状況の取得（後方互換性のため）"""
    try:
        db_manager = DatabaseManager.get_instance()
        usage_repo = db_manager.get_usage_statistics_repository()
        # 簡易的な実装 - 必要に応じて期間を指定
        import datetime
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=30)
        return usage_repo.get_usage_records(start_date, end_date)
    except Exception as e:
        raise DatabaseError(f"使用状況の取得に失敗しました: {str(e)}")


def get_settings_collection(app_type=None):
    """設定の取得（後方互換性のため）"""
    try:
        db_manager = DatabaseManager.get_instance()
        settings_repo = db_manager.get_settings_repository()
        settings = settings_repo.get_settings_by_app_type(app_type)
        # 辞書形式に変換（既存コードとの互換性のため）
        return [
            {
                'setting_id': s.setting_id,
                'app_type': s.app_type,
                'selected_department': s.selected_department,
                'selected_model': s.selected_model,
                'selected_document_type': s.selected_document_type,
                'selected_doctor': s.selected_doctor,
                'updated_at': s.updated_at
            }
            for s in settings
        ]
    except Exception as e:
        raise DatabaseError(f"設定の取得に失敗しました: {str(e)}")


# リポジトリのシングルトンインスタンス取得用関数
def get_prompt_repository() -> PromptRepository:
    """プロンプトリポジトリのシングルトンインスタンスを取得"""
    return DatabaseManager.get_instance().get_prompt_repository()


def get_usage_statistics_repository() -> UsageStatisticsRepository:
    """使用統計リポジトリのシングルトンインスタンスを取得"""
    return DatabaseManager.get_instance().get_usage_statistics_repository()


def get_settings_repository() -> SettingsRepository:
    """設定リポジトリのシングルトンインスタンスを取得"""
    return DatabaseManager.get_instance().get_settings_repository()