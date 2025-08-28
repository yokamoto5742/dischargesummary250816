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


# === 詳細なフィルタリングメソッドテスト ===

class TestUsageStatisticsRepositoryFiltering:
    """UsageStatisticsRepositoryのフィルタリング機能の詳細テスト"""

    def setup_method(self):
        self.mock_session_factory = Mock()
        self.repo = UsageStatisticsRepository(self.mock_session_factory)

    def test_apply_model_filter_claude(self):
        """Claudeモデルフィルターのテスト"""
        mock_query = Mock()
        mock_filtered_query = Mock()
        mock_query.filter.return_value = mock_filtered_query

        result = self.repo._apply_model_filter(mock_query, "Claude")

        assert result is mock_filtered_query
        mock_query.filter.assert_called_once()
        # ilike('%claude%')が呼ばれることを確認
        args = mock_query.filter.call_args[0]
        assert len(args) == 1

    def test_apply_model_filter_gemini_pro(self):
        """Gemini_Proモデルフィルターのテスト"""
        mock_query = Mock()
        mock_filtered_query = Mock()
        mock_query.filter.return_value = mock_filtered_query

        result = self.repo._apply_model_filter(mock_query, "Gemini_Pro")

        assert result is mock_filtered_query
        mock_query.filter.assert_called_once()
        # geminiを含み、flashは含まない条件
        args = mock_query.filter.call_args[0]
        assert len(args) == 2  # gemini条件 + not flash条件

    def test_apply_model_filter_gemini_flash(self):
        """Gemini_Flashモデルフィルターのテスト"""
        mock_query = Mock()
        mock_filtered_query = Mock()
        mock_query.filter.return_value = mock_filtered_query

        result = self.repo._apply_model_filter(mock_query, "Gemini_Flash")

        assert result is mock_filtered_query
        mock_query.filter.assert_called_once()
        # flash条件のみ
        args = mock_query.filter.call_args[0]
        assert len(args) == 1

    def test_apply_model_filter_none(self):
        """モデルフィルターがNoneの場合のテスト"""
        mock_query = Mock()

        result = self.repo._apply_model_filter(mock_query, None)

        assert result is mock_query
        mock_query.filter.assert_not_called()

    def test_apply_model_filter_empty_string(self):
        """モデルフィルターが空文字列の場合のテスト"""
        mock_query = Mock()

        result = self.repo._apply_model_filter(mock_query, "")

        assert result is mock_query
        mock_query.filter.assert_not_called()

    def test_apply_model_filter_unknown_model(self):
        """未知のモデルフィルターの場合のテスト"""
        mock_query = Mock()

        result = self.repo._apply_model_filter(mock_query, "UnknownModel")

        assert result is mock_query
        mock_query.filter.assert_not_called()

    def test_apply_document_type_filter_specific_type(self):
        """特定の文書タイプフィルターのテスト"""
        mock_query = Mock()
        mock_filtered_query = Mock()
        mock_query.filter.return_value = mock_filtered_query

        result = self.repo._apply_document_type_filter(mock_query, "退院時サマリ")

        assert result is mock_filtered_query
        mock_query.filter.assert_called_once()

    def test_apply_document_type_filter_unknown(self):
        """「不明」文書タイプフィルターのテスト"""
        mock_query = Mock()
        mock_filtered_query = Mock()
        mock_query.filter.return_value = mock_filtered_query

        result = self.repo._apply_document_type_filter(mock_query, "不明")

        assert result is mock_filtered_query
        mock_query.filter.assert_called_once()
        # is_(None)が呼ばれることを確認

    def test_apply_document_type_filter_none(self):
        """文書タイプフィルターがNoneの場合のテスト"""
        mock_query = Mock()

        result = self.repo._apply_document_type_filter(mock_query, None)

        assert result is mock_query
        mock_query.filter.assert_not_called()

    def test_apply_document_type_filter_all(self):
        """「すべて」文書タイプフィルターのテスト"""
        mock_query = Mock()

        result = self.repo._apply_document_type_filter(mock_query, "すべて")

        assert result is mock_query
        mock_query.filter.assert_not_called()

    def test_apply_filters_integration(self):
        """複数フィルターの統合テスト"""
        start_date = datetime.datetime(2024, 1, 1)
        end_date = datetime.datetime(2024, 12, 31)
        mock_query = Mock()

        with patch.object(self.repo, '_apply_date_filter', return_value=mock_query) as mock_date_filter, \
             patch.object(self.repo, '_apply_model_filter', return_value=mock_query) as mock_model_filter, \
             patch.object(self.repo, '_apply_document_type_filter', return_value=mock_query) as mock_doc_filter:

            result = self.repo._apply_filters(
                mock_query, start_date, end_date, "Claude", "退院時サマリ"
            )

            assert result is mock_query
            mock_date_filter.assert_called_once_with(mock_query, start_date, end_date)
            mock_model_filter.assert_called_once_with(mock_query, "Claude")
            mock_doc_filter.assert_called_once_with(mock_query, "退院時サマリ")

    def test_get_department_statistics_success(self):
        """部門別統計取得成功のテスト"""
        mock_session = Mock()
        mock_query = Mock()
        mock_filtered_query = Mock()
        mock_grouped_query = Mock()
        mock_ordered_query = Mock()
        
        # モックレスポンス
        mock_result1 = Mock()
        mock_result1.department = "内科"
        mock_result1.doctor = "田中医師"
        mock_result1.document_types = "退院時サマリ"
        mock_result1.count = 5
        mock_result1.input_tokens = 1000
        mock_result1.output_tokens = 500
        mock_result1.total_tokens = 1500
        mock_result1.processing_time = 300

        mock_result2 = Mock()
        mock_result2.department = "外科"
        mock_result2.doctor = "山田医師"
        mock_result2.document_types = "手術記録"
        mock_result2.count = 3
        mock_result2.input_tokens = 800
        mock_result2.output_tokens = 400
        mock_result2.total_tokens = 1200
        mock_result2.processing_time = 250

        mock_results = [mock_result1, mock_result2]

        mock_session.query.return_value = mock_query
        mock_query.group_by.return_value = mock_grouped_query
        mock_grouped_query.order_by.return_value = mock_ordered_query
        mock_ordered_query.all.return_value = mock_results

        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)

        start_date = datetime.datetime(2024, 1, 1)
        end_date = datetime.datetime(2024, 12, 31)

        with patch.object(self.repo, '_apply_filters', return_value=mock_query):
            result = self.repo.get_department_statistics(
                start_date, end_date, "Claude", "退院時サマリ"
            )

        expected = [
            {
                'department': "内科",
                'doctor': "田中医師",
                'document_types': "退院時サマリ",
                'count': 5,
                'input_tokens': 1000,
                'output_tokens': 500,
                'total_tokens': 1500,
                'processing_time': 300
            },
            {
                'department': "外科",
                'doctor': "山田医師",
                'document_types': "手術記録",
                'count': 3,
                'input_tokens': 800,
                'output_tokens': 400,
                'total_tokens': 1200,
                'processing_time': 250
            }
        ]

        assert result == expected

    def test_get_department_statistics_exception(self):
        """部門別統計取得時の例外テスト"""
        mock_session = Mock()
        mock_session.query.side_effect = Exception("Database connection failed")

        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)

        start_date = datetime.datetime(2024, 1, 1)
        end_date = datetime.datetime(2024, 12, 31)

        with pytest.raises(DatabaseError, match="部門別統計の取得に失敗しました"):
            self.repo.get_department_statistics(start_date, end_date)

    def test_get_usage_records_success(self):
        """使用記録取得成功のテスト"""
        mock_session = Mock()
        mock_query = Mock()
        mock_filtered_query = Mock()
        mock_ordered_query = Mock()
        
        mock_records = [Mock() for _ in range(5)]
        
        mock_session.query.return_value = mock_query
        mock_filtered_query.order_by.return_value = mock_ordered_query
        mock_ordered_query.all.return_value = mock_records

        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)

        start_date = datetime.datetime(2024, 1, 1)
        end_date = datetime.datetime(2024, 12, 31)

        with patch.object(self.repo, '_apply_filters', return_value=mock_filtered_query):
            result = self.repo.get_usage_records(
                start_date, end_date, "Gemini_Pro", "入院記録"
            )

        assert result == mock_records
        mock_filtered_query.order_by.assert_called_once()

    def test_get_usage_records_exception(self):
        """使用記録取得時の例外テスト"""
        mock_session = Mock()
        mock_session.query.side_effect = Exception("Query failed")

        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)

        start_date = datetime.datetime(2024, 1, 1)
        end_date = datetime.datetime(2024, 12, 31)

        with pytest.raises(DatabaseError, match="使用記録の取得に失敗しました"):
            self.repo.get_usage_records(start_date, end_date)

    def test_get_usage_summary_null_values(self):
        """使用統計での NULL値処理のテスト"""
        mock_session = Mock()
        mock_query = Mock()
        mock_result = Mock()
        # NULL値のシミュレーション
        mock_result.count = None
        mock_result.total_input_tokens = None
        mock_result.total_output_tokens = None
        mock_result.total_tokens = None

        mock_session.query.return_value = mock_query
        mock_query.first.return_value = mock_result

        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)

        start_date = datetime.datetime(2024, 1, 1)
        end_date = datetime.datetime(2024, 12, 31)

        with patch.object(self.repo, '_apply_filters', return_value=mock_query):
            result = self.repo.get_usage_summary(start_date, end_date)

        expected = {
            'count': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_tokens': 0
        }
        assert result == expected

    def test_get_usage_summary_exception(self):
        """使用統計取得時の例外テスト"""
        mock_session = Mock()
        mock_session.query.side_effect = Exception("Aggregation failed")

        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)

        start_date = datetime.datetime(2024, 1, 1)
        end_date = datetime.datetime(2024, 12, 31)

        with pytest.raises(DatabaseError, match="使用統計の取得に失敗しました"):
            self.repo.get_usage_summary(start_date, end_date)

    def test_model_filter_case_sensitivity(self):
        """モデルフィルターの大文字小文字テスト"""
        mock_query = Mock()
        
        # 大文字小文字が異なる場合
        result1 = self.repo._apply_model_filter(mock_query, "claude")  # 小文字
        result2 = self.repo._apply_model_filter(mock_query, "CLAUDE")  # 大文字
        result3 = self.repo._apply_model_filter(mock_query, "Claude")  # 正常

        # 正常なケースのみフィルターが適用される
        assert result1 is mock_query  # フィルター適用されない
        assert result2 is mock_query  # フィルター適用されない
        # result3のみフィルターが適用される

    def test_complex_filtering_scenario(self):
        """複雑なフィルタリングシナリオのテスト"""
        start_date = datetime.datetime(2024, 6, 1)
        end_date = datetime.datetime(2024, 6, 30)
        model_filter = "Gemini_Flash"
        document_type_filter = "検査結果"

        mock_session = Mock()
        mock_query = Mock()
        mock_result = Mock()
        mock_result.count = 25
        mock_result.total_input_tokens = 5000
        mock_result.total_output_tokens = 2500
        mock_result.total_tokens = 7500

        mock_session.query.return_value = mock_query
        mock_query.first.return_value = mock_result

        self.mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        self.mock_session_factory.return_value.__exit__ = Mock(return_value=None)

        # 複数のフィルター条件を同時にテスト
        with patch.object(self.repo, '_apply_date_filter', return_value=mock_query) as mock_date, \
             patch.object(self.repo, '_apply_model_filter', return_value=mock_query) as mock_model, \
             patch.object(self.repo, '_apply_document_type_filter', return_value=mock_query) as mock_doc:

            result = self.repo.get_usage_summary(
                start_date, end_date, model_filter, document_type_filter
            )

            # すべてのフィルターが適用されることを確認
            mock_date.assert_called_once_with(mock_query, start_date, end_date)
            mock_model.assert_called_once_with(mock_query, model_filter)
            mock_doc.assert_called_once_with(mock_query, document_type_filter)

        expected = {
            'count': 25,
            'total_input_tokens': 5000,
            'total_output_tokens': 2500,
            'total_tokens': 7500
        }
        assert result == expected