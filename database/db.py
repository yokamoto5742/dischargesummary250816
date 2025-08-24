import os

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

    def get_prompt_repository(self) -> PromptRepository:
        return PromptRepository(self.get_session_factory())

    def get_usage_statistics_repository(self) -> UsageStatisticsRepository:
        return UsageStatisticsRepository(self.get_session_factory())

    def get_settings_repository(self) -> SettingsRepository:
        return SettingsRepository(self.get_session_factory())


def get_prompt_repository() -> PromptRepository:
    return DatabaseManager.get_instance().get_prompt_repository()


def get_usage_statistics_repository() -> UsageStatisticsRepository:
    return DatabaseManager.get_instance().get_usage_statistics_repository()


def get_settings_repository() -> SettingsRepository:
    return DatabaseManager.get_instance().get_settings_repository()
