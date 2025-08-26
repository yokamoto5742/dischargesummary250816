import datetime
from unittest.mock import Mock, patch

import pytest

from database.models import Prompt, AppSetting
from database.repositories import BaseRepository, PromptRepository, UsageStatisticsRepository, SettingsRepository
from utils.exceptions import DatabaseError


class TestBaseRepository:
    
    def test_init(self):
        mock_session_factory = Mock()
        repo = BaseRepository(mock_session_factory)
        assert repo.session_factory is mock_session_factory

    def test_get_session(self):
        mock_session_factory = Mock()
        mock_session = Mock()
        mock_session_factory.return_value = mock_session
        
        repo = BaseRepository(mock_session_factory)
        session = repo.get_session()
        
        assert session is mock_session
        mock_session_factory.assert_called_once()


class TestPromptRepository:
    
    def setup_method(self):
        self.mock_session_factory = Mock()
        self.repo = PromptRepository(self.mock_session_factory)

    def test_get_by_keys_success(self):
        mock_session = Mock()
        mock_prompt = Mock(spec=Prompt)
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_prompt
        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        
        result = self.repo.get_by_keys("dept", "doc_type", "doctor")
        
        assert result is mock_prompt
        mock_session.query.assert_called_once_with(Prompt)

    def test_get_by_keys_exception(self):
        mock_session = Mock()
        mock_session.query.side_effect = Exception("Database error")
        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        
        with pytest.raises(DatabaseError) as exc_info:
            self.repo.get_by_keys("dept", "doc_type", "doctor")
        assert "プロンプトの取得に失敗しました" in str(exc_info.value)

    def test_get_default_prompt_success(self):
        mock_session = Mock()
        mock_prompt = Mock(spec=Prompt)
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_prompt
        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        
        result = self.repo.get_default_prompt()
        
        assert result is mock_prompt

    def test_get_default_prompt_exception(self):
        mock_session = Mock()
        mock_session.query.side_effect = Exception("Database error")
        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        
        with pytest.raises(DatabaseError) as exc_info:
            self.repo.get_default_prompt()
        assert "デフォルトプロンプトの取得に失敗しました" in str(exc_info.value)

    @patch('database.repositories.datetime')
    def test_create_or_update_new_prompt(self, mock_datetime):
        mock_now = datetime.datetime(2023, 1, 1, 12)
        mock_datetime.datetime.now.return_value = mock_now
        
        mock_session = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None  # No existing prompt
        
        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        
        success, message = self.repo.create_or_update("dept", "doc_type", "doctor", "content", "model")
        
        assert success is True
        assert "新規作成" in message
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch('database.repositories.datetime')
    def test_create_or_update_existing_prompt(self, mock_datetime):
        mock_now = datetime.datetime(2023, 1, 1, 12)
        mock_datetime.datetime.now.return_value = mock_now
        
        mock_session = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_existing_prompt = Mock()
        
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_existing_prompt
        
        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        
        success, message = self.repo.create_or_update("dept", "doc_type", "doctor", "new_content", "new_model")
        
        assert success is True
        assert "更新" in message
        assert mock_existing_prompt.content == "new_content"
        assert mock_existing_prompt.selected_model == "new_model"
        assert mock_existing_prompt.updated_at == mock_now
        mock_session.commit.assert_called_once()

    def test_create_or_update_exception(self):
        mock_session = Mock()
        mock_session.query.side_effect = Exception("Database error")
        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        
        with pytest.raises(DatabaseError) as exc_info:
            self.repo.create_or_update("dept", "doc_type", "doctor", "content")
        assert "プロンプトの作成/更新に失敗しました" in str(exc_info.value)

    def test_delete_by_keys_success(self):
        mock_session = Mock()
        mock_prompt = Mock()
        mock_prompt.is_default = False
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_prompt
        
        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        
        success, message = self.repo.delete_by_keys("dept", "doc_type", "doctor")
        
        assert success is True
        assert "プロンプトを削除しました" in message
        mock_session.delete.assert_called_once_with(mock_prompt)
        mock_session.commit.assert_called_once()

    def test_delete_by_keys_not_found(self):
        mock_session = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None
        
        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        
        success, message = self.repo.delete_by_keys("dept", "doc_type", "doctor")
        
        assert success is False
        assert "プロンプトが見つかりません" in message

    def test_delete_by_keys_default_prompt(self):
        mock_session = Mock()
        mock_prompt = Mock()
        mock_prompt.is_default = True
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_prompt
        
        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        
        success, message = self.repo.delete_by_keys("default", "doc_type", "doctor")
        
        assert success is False
        assert "デフォルトプロンプトは削除できません" in message

    def test_get_all_success(self):
        mock_session = Mock()
        mock_prompts = [Mock(spec=Prompt) for _ in range(3)]
        mock_query = Mock()
        mock_order_by = Mock()
        
        mock_session.query.return_value = mock_query
        mock_query.order_by.return_value = mock_order_by
        mock_order_by.all.return_value = mock_prompts
        
        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        
        result = self.repo.get_all()
        
        assert result == mock_prompts
        mock_session.query.assert_called_once_with(Prompt)


class TestUsageStatisticsRepository:
    
    def setup_method(self):
        self.mock_session_factory = Mock()
        self.repo = UsageStatisticsRepository(self.mock_session_factory)

    def test_save_usage_success(self):
        mock_session = Mock()
        usage_data = {
            "app_type": "test_app",
            "document_types": "退院時サマリ",
            "model_detail": "gpt-4",
            "department": "内科",
            "doctor": "田中医師",
            "input_tokens": 100,
            "output_tokens": 200,
            "total_tokens": 300,
            "processing_time": 5000
        }
        
        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        
        self.repo.save_usage(usage_data)
        
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_save_usage_exception(self):
        mock_session = Mock()
        mock_session.add.side_effect = Exception("Database error")
        usage_data = {"field": "value"}
        
        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        
        with pytest.raises(DatabaseError) as exc_info:
            self.repo.save_usage(usage_data)
        assert "使用統計の保存に失敗しました" in str(exc_info.value)

    def test_apply_date_filter(self):
        start_date = datetime.datetime(2023, 1, 1)
        end_date = datetime.datetime(2023, 12, 31)
        mock_query = Mock()
        mock_filtered_query = Mock()
        mock_query.filter.return_value = mock_filtered_query
        
        result = self.repo._apply_date_filter(mock_query, start_date, end_date)
        
        assert result is mock_filtered_query
        mock_query.filter.assert_called_once()

    def test_apply_model_filter_all(self):
        mock_query = Mock()
        
        result = self.repo._apply_model_filter(mock_query, "すべて")
        
        assert result is mock_query

    def test_apply_model_filter_gemini_pro(self):
        mock_query = Mock()
        mock_filtered_query = Mock()
        mock_query.filter.return_value = mock_filtered_query
        
        result = self.repo._apply_model_filter(mock_query, "Gemini_Pro")
        
        assert result is mock_filtered_query
        mock_query.filter.assert_called_once()

    def test_apply_document_type_filter_all(self):
        mock_query = Mock()
        
        result = self.repo._apply_document_type_filter(mock_query, "すべて")
        
        assert result is mock_query

    def test_get_usage_summary_success(self):
        mock_session = Mock()
        mock_query = Mock()
        mock_result = Mock()
        mock_result.count = 10
        mock_result.total_input_tokens = 1000
        mock_result.total_output_tokens = 500
        mock_result.total_tokens = 1500
        
        mock_session.query.return_value = mock_query
        mock_query.first.return_value = mock_result
        
        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        
        start_date = datetime.datetime(2023, 1, 1)
        end_date = datetime.datetime(2023, 12, 31)
        
        with patch.object(self.repo, '_apply_filters', return_value=mock_query):
            result = self.repo.get_usage_summary(start_date, end_date)
        
        expected = {
            'count': 10,
            'total_input_tokens': 1000,
            'total_output_tokens': 500,
            'total_tokens': 1500
        }
        assert result == expected


class TestSettingsRepository:
    
    def setup_method(self):
        self.mock_session_factory = Mock()
        self.repo = SettingsRepository(self.mock_session_factory)

    @patch('database.repositories.datetime')
    def test_save_user_settings_new(self, mock_datetime):
        mock_now = datetime.datetime(2023, 1, 1, 12)
        mock_datetime.datetime.now.return_value = mock_now
        
        mock_session = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = None  # No existing setting
        
        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        
        self.repo.save_user_settings("id", "app_type", "dept", "model", "doc_type", "doctor")
        
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch('database.repositories.datetime')
    def test_save_user_settings_existing(self, mock_datetime):
        mock_now = datetime.datetime(2023, 1, 1, 12)
        mock_datetime.datetime.now.return_value = mock_now
        
        mock_session = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_existing = Mock()
        
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_existing
        
        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        
        self.repo.save_user_settings("id", "app_type", "dept", "model", "doc_type", "doctor")
        
        assert mock_existing.selected_department == "dept"
        assert mock_existing.selected_model == "model"
        assert mock_existing.selected_document_type == "doc_type"
        assert mock_existing.selected_doctor == "doctor"
        assert mock_existing.updated_at == mock_now
        mock_session.commit.assert_called_once()

    def test_load_user_settings_success(self):
        mock_session = Mock()
        mock_setting = Mock(spec=AppSetting)
        mock_query = Mock()
        mock_filter = Mock()
        
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.first.return_value = mock_setting
        
        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        
        result = self.repo.load_user_settings("setting_id")
        
        assert result is mock_setting
        mock_session.query.assert_called_once_with(AppSetting)

    def test_get_settings_by_app_type_with_filter(self):
        mock_session = Mock()
        mock_settings = [Mock(spec=AppSetting) for _ in range(3)]
        mock_query = Mock()
        mock_filtered_query = Mock()
        
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filtered_query
        mock_filtered_query.all.return_value = mock_settings
        
        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        
        result = self.repo.get_settings_by_app_type("app_type")
        
        assert result == mock_settings
        mock_query.filter.assert_called_once()

    def test_get_settings_by_app_type_no_filter(self):
        mock_session = Mock()
        mock_settings = [Mock(spec=AppSetting) for _ in range(3)]
        mock_query = Mock()
        
        mock_session.query.return_value = mock_query
        mock_query.all.return_value = mock_settings
        
        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        
        result = self.repo.get_settings_by_app_type()
        
        assert result == mock_settings
        mock_query.filter.assert_not_called()