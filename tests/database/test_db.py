import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.pool import QueuePool

from database.db import DatabaseManager, get_prompt_repository, get_usage_statistics_repository, get_settings_repository
from database.repositories import PromptRepository, UsageStatisticsRepository, SettingsRepository
from utils.exceptions import DatabaseError


class TestDatabaseManager:
    
    def setup_method(self):
        DatabaseManager._instance = None
        DatabaseManager._engine = None
        DatabaseManager._session_factory = None
        DatabaseManager._scoped_session = None

    @patch('database.db.create_engine')
    @patch('database.db.sessionmaker')
    @patch('database.db.scoped_session')
    @patch('database.db.Base')
    def test_init_with_database_url(self, mock_base, mock_scoped_session, mock_sessionmaker, mock_create_engine):
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        mock_session_factory = Mock()
        mock_sessionmaker.return_value = mock_session_factory
        mock_scoped = Mock()
        mock_scoped_session.return_value = mock_scoped
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgres://user:pass@host:5432/db'}):
            db_manager = DatabaseManager()
            
            mock_create_engine.assert_called_once()
            call_args = mock_create_engine.call_args[0]
            assert 'postgresql://user:pass@host:5432/db?sslmode=require' in call_args[0]
            
            mock_sessionmaker.assert_called_once_with(bind=mock_engine)
            mock_scoped_session.assert_called_once_with(mock_session_factory)
            mock_base.metadata.create_all.assert_called_once_with(mock_engine)

    @patch('database.db.create_engine')
    def test_init_with_config_values(self, mock_create_engine):
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        with patch.dict(os.environ, {}, clear=True):
            with patch('database.db.POSTGRES_HOST', 'localhost'), \
                 patch('database.db.POSTGRES_PORT', '5432'), \
                 patch('database.db.POSTGRES_USER', 'user'), \
                 patch('database.db.POSTGRES_PASSWORD', 'pass'), \
                 patch('database.db.POSTGRES_DB', 'testdb'), \
                 patch('database.db.POSTGRES_SSL', 'require'):
                
                DatabaseManager()
                
                mock_create_engine.assert_called_once()
                call_args = mock_create_engine.call_args[0]
                assert 'postgresql://user:pass@localhost:5432/testdb?sslmode=require' in call_args[0]

    def test_init_missing_config(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch('database.db.POSTGRES_HOST', None):
                with pytest.raises(DatabaseError) as exc_info:
                    DatabaseManager()
                assert "PostgreSQL接続情報が設定されていません" in str(exc_info.value)

    @patch('database.db.create_engine')
    def test_init_database_connection_error(self, mock_create_engine):
        mock_create_engine.side_effect = Exception("Connection failed")
        
        with patch.dict(os.environ, {}, clear=True):
            with patch('database.db.POSTGRES_HOST', 'localhost'), \
                 patch('database.db.POSTGRES_PORT', '5432'), \
                 patch('database.db.POSTGRES_USER', 'user'), \
                 patch('database.db.POSTGRES_PASSWORD', 'pass'), \
                 patch('database.db.POSTGRES_DB', 'testdb'):
                
                with pytest.raises(DatabaseError) as exc_info:
                    DatabaseManager()
                assert "PostgreSQLへの接続に失敗しました" in str(exc_info.value)

    def test_database_url_parsing_error(self):
        with patch.dict(os.environ, {'DATABASE_URL': 'invalid-url'}):
            with pytest.raises(DatabaseError) as exc_info:
                DatabaseManager()
            assert "DATABASE_URLの解析に失敗しました" in str(exc_info.value)

    @patch('database.db.create_engine')
    @patch('database.db.sessionmaker')
    @patch('database.db.scoped_session')
    @patch('database.db.Base')
    def test_singleton_pattern(self, mock_base, mock_scoped_session, mock_sessionmaker, mock_create_engine):
        mock_create_engine.return_value = Mock()
        mock_sessionmaker.return_value = Mock()
        mock_scoped_session.return_value = Mock()
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgres://user:pass@host:5432/db'}):
            instance1 = DatabaseManager.get_instance()
            instance2 = DatabaseManager.get_instance()
            
            assert instance1 is instance2

    @patch('database.db.create_engine')
    @patch('database.db.sessionmaker')
    @patch('database.db.scoped_session')
    @patch('database.db.Base')
    def test_get_engine(self, mock_base, mock_scoped_session, mock_sessionmaker, mock_create_engine):
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgres://user:pass@host:5432/db'}):
            DatabaseManager()
            engine = DatabaseManager.get_engine()
            assert engine is mock_engine

    @patch('database.db.create_engine')
    @patch('database.db.sessionmaker')
    @patch('database.db.scoped_session')
    @patch('database.db.Base')
    def test_get_session_factory(self, mock_base, mock_scoped_session, mock_sessionmaker, mock_create_engine):
        mock_session_factory = Mock()
        mock_sessionmaker.return_value = mock_session_factory
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgres://user:pass@host:5432/db'}):
            DatabaseManager()
            session_factory = DatabaseManager.get_session_factory()
            assert session_factory is mock_session_factory

    @patch('database.db.create_engine')
    @patch('database.db.sessionmaker')
    @patch('database.db.scoped_session')
    @patch('database.db.Base')
    def test_get_scoped_session(self, mock_base, mock_scoped_session, mock_sessionmaker, mock_create_engine):
        mock_scoped = Mock()
        mock_scoped_session.return_value = mock_scoped
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgres://user:pass@host:5432/db'}):
            DatabaseManager()
            scoped_session = DatabaseManager.get_scoped_session()
            assert scoped_session is mock_scoped

    @patch('database.db.create_engine')
    @patch('database.db.sessionmaker')
    @patch('database.db.scoped_session')
    @patch('database.db.Base')
    def test_get_repositories(self, mock_base, mock_scoped_session, mock_sessionmaker, mock_create_engine):
        mock_session_factory = Mock()
        mock_sessionmaker.return_value = mock_session_factory
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgres://user:pass@host:5432/db'}):
            db_manager = DatabaseManager()
            
            prompt_repo = db_manager.get_prompt_repository()
            assert isinstance(prompt_repo, PromptRepository)
            
            usage_repo = db_manager.get_usage_statistics_repository()
            assert isinstance(usage_repo, UsageStatisticsRepository)
            
            settings_repo = db_manager.get_settings_repository()
            assert isinstance(settings_repo, SettingsRepository)


class TestGlobalFunctions:
    
    @patch('database.db.DatabaseManager.get_instance')
    def test_get_prompt_repository(self, mock_get_instance):
        mock_instance = Mock()
        mock_repo = Mock(spec=PromptRepository)
        mock_instance.get_prompt_repository.return_value = mock_repo
        mock_get_instance.return_value = mock_instance
        
        result = get_prompt_repository()
        
        assert result is mock_repo
        mock_get_instance.assert_called_once()
        mock_instance.get_prompt_repository.assert_called_once()

    @patch('database.db.DatabaseManager.get_instance')
    def test_get_usage_statistics_repository(self, mock_get_instance):
        mock_instance = Mock()
        mock_repo = Mock(spec=UsageStatisticsRepository)
        mock_instance.get_usage_statistics_repository.return_value = mock_repo
        mock_get_instance.return_value = mock_instance
        
        result = get_usage_statistics_repository()
        
        assert result is mock_repo
        mock_get_instance.assert_called_once()
        mock_instance.get_usage_statistics_repository.assert_called_once()

    @patch('database.db.DatabaseManager.get_instance')
    def test_get_settings_repository(self, mock_get_instance):
        mock_instance = Mock()
        mock_repo = Mock(spec=SettingsRepository)
        mock_instance.get_settings_repository.return_value = mock_repo
        mock_get_instance.return_value = mock_instance
        
        result = get_settings_repository()
        
        assert result is mock_repo
        mock_get_instance.assert_called_once()
        mock_instance.get_settings_repository.assert_called_once()