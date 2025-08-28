import pytest
import datetime
from unittest.mock import Mock, patch, MagicMock
from services.statistics_service import StatisticsService
import pytz


class TestStatisticsService:

    @patch('services.statistics_service.get_usage_statistics_repository')
    @patch('services.statistics_service.datetime')
    @patch('services.statistics_service.APP_TYPE', 'test_app')
    def test_save_usage_to_database_success(self, mock_datetime, mock_get_repo):
        """正常なデータベース保存のテスト"""
        # モックの設定
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        
        # 固定の日時を設定
        fixed_time = datetime.datetime(2024, 1, 15, 10, 30, 0)
        mock_jst_time = fixed_time.replace(tzinfo=pytz.timezone('Asia/Tokyo'))
        mock_datetime.datetime.now.return_value.astimezone.return_value = mock_jst_time
        
        # テストデータ
        result = {
            "model_detail": "claude-3-sonnet",
            "input_tokens": 100,
            "output_tokens": 200,
            "processing_time": 5.75
        }
        
        session_params = {
            "selected_document_type": "退院時サマリ",
            "selected_department": "内科",
            "selected_doctor": "田中医師"
        }
        
        # メソッド実行
        StatisticsService.save_usage_to_database(result, session_params)
        
        # 検証
        expected_usage_data = {
            "date": mock_jst_time,
            "app_type": "test_app",
            "document_types": "退院時サマリ",
            "model_detail": "claude-3-sonnet",
            "department": "内科",
            "doctor": "田中医師",
            "input_tokens": 100,
            "output_tokens": 200,
            "total_tokens": 300,
            "processing_time": 6  # 四捨五入される
        }
        
        mock_repo.save_usage.assert_called_once_with(expected_usage_data)

    @patch('services.statistics_service.get_usage_statistics_repository')
    @patch('streamlit.warning')
    def test_save_usage_to_database_exception_handling(self, mock_st_warning, mock_get_repo):
        """データベース保存時の例外処理テスト"""
        # リポジトリで例外を発生させる
        mock_repo = Mock()
        mock_repo.save_usage.side_effect = Exception("Database connection failed")
        mock_get_repo.return_value = mock_repo
        
        result = {
            "model_detail": "claude-3-sonnet",
            "input_tokens": 50,
            "output_tokens": 100,
            "processing_time": 3.0
        }
        
        session_params = {
            "selected_document_type": "入院記録",
            "selected_department": "外科",
            "selected_doctor": "山田医師"
        }
        
        # 例外が発生しても処理が継続されることを確認
        StatisticsService.save_usage_to_database(result, session_params)
        
        # 警告メッセージが表示されることを確認
        mock_st_warning.assert_called_once_with(
            "データベース保存中にエラーが発生しました: Database connection failed"
        )

    @patch('services.statistics_service.get_usage_statistics_repository')
    @patch('services.statistics_service.datetime')
    @patch('services.statistics_service.APP_TYPE', 'medical_docs')
    def test_save_usage_to_database_zero_tokens(self, mock_datetime, mock_get_repo):
        """トークン数が0の場合のテスト"""
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        
        fixed_time = datetime.datetime(2024, 2, 1, 14, 0, 0)
        mock_jst_time = fixed_time.replace(tzinfo=pytz.timezone('Asia/Tokyo'))
        mock_datetime.datetime.now.return_value.astimezone.return_value = mock_jst_time
        
        result = {
            "model_detail": "gemini-1.5-pro",
            "input_tokens": 0,
            "output_tokens": 0,
            "processing_time": 1.0
        }
        
        session_params = {
            "selected_document_type": "検査結果",
            "selected_department": "検査科",
            "selected_doctor": "default"
        }
        
        StatisticsService.save_usage_to_database(result, session_params)
        
        expected_usage_data = {
            "date": mock_jst_time,
            "app_type": "medical_docs",
            "document_types": "検査結果",
            "model_detail": "gemini-1.5-pro",
            "department": "検査科",
            "doctor": "default",
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "processing_time": 1
        }
        
        mock_repo.save_usage.assert_called_once_with(expected_usage_data)

    @patch('services.statistics_service.get_usage_statistics_repository')
    @patch('services.statistics_service.datetime')
    @patch('services.statistics_service.APP_TYPE', 'MediDocs')
    def test_save_usage_to_database_large_values(self, mock_datetime, mock_get_repo):
        """大きな値での保存テスト"""
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        
        fixed_time = datetime.datetime(2024, 3, 1, 9, 15, 30)
        mock_jst_time = fixed_time.replace(tzinfo=pytz.timezone('Asia/Tokyo'))
        mock_datetime.datetime.now.return_value.astimezone.return_value = mock_jst_time
        
        result = {
            "model_detail": "claude-3-opus",
            "input_tokens": 50000,
            "output_tokens": 25000,
            "processing_time": 120.456
        }
        
        session_params = {
            "selected_document_type": "診療記録",
            "selected_department": "総合診療科",
            "selected_doctor": "佐藤部長"
        }
        
        StatisticsService.save_usage_to_database(result, session_params)
        
        expected_usage_data = {
            "date": mock_jst_time,
            "app_type": "MediDocs",
            "document_types": "診療記録",
            "model_detail": "claude-3-opus",
            "department": "総合診療科",
            "doctor": "佐藤部長",
            "input_tokens": 50000,
            "output_tokens": 25000,
            "total_tokens": 75000,
            "processing_time": 120  # 四捨五入
        }
        
        mock_repo.save_usage.assert_called_once_with(expected_usage_data)

    @patch('streamlit.session_state', new_callable=MagicMock)
    @patch('streamlit.info')
    def test_handle_success_result_with_model_switching(self, mock_st_info, mock_st_state):
        """モデル切り替えありの成功結果処理テスト"""
        result = {
            "output_summary": "生成されたサマリテキスト",
            "parsed_summary": {"sections": ["症状", "診断", "治療"]},
            "model_switched": True,
            "original_model": "Claude",
            "model_detail": "gemini-1.5-pro",
            "input_tokens": 1500,
            "output_tokens": 800,
            "processing_time": 45.2
        }
        
        session_params = {
            "selected_department": "循環器内科",
            "selected_doctor": "心臓医師"
        }
        
        with patch.object(StatisticsService, 'save_usage_to_database') as mock_save:
            StatisticsService.handle_success_result(result, session_params)
            
            # セッション状態の更新を確認
            assert mock_st_state.output_summary == "生成されたサマリテキスト"
            assert mock_st_state.parsed_summary == {"sections": ["症状", "診断", "治療"]}
            
            # モデル切り替えメッセージの表示を確認
            mock_st_info.assert_called_once_with(
                "⚠️ 入力テキストが長いためClaude からGemini_Proに切り替えました"
            )
            
            # データベース保存が呼ばれることを確認
            mock_save.assert_called_once_with(result, session_params)

    @patch('streamlit.session_state', new_callable=MagicMock)
    @patch('streamlit.info')
    def test_handle_success_result_without_model_switching(self, mock_st_info, mock_st_state):
        """モデル切り替えなしの成功結果処理テスト"""
        result = {
            "output_summary": "通常のサマリテキスト",
            "parsed_summary": {"title": "退院時サマリ", "content": "詳細内容"},
            "model_switched": False,
            "model_detail": "claude-3-sonnet",
            "input_tokens": 500,
            "output_tokens": 300,
            "processing_time": 15.8
        }
        
        session_params = {
            "selected_department": "呼吸器内科",
            "selected_doctor": "肺医師"
        }
        
        with patch.object(StatisticsService, 'save_usage_to_database') as mock_save:
            StatisticsService.handle_success_result(result, session_params)
            
            # セッション状態の更新を確認
            assert mock_st_state.output_summary == "通常のサマリテキスト"
            assert mock_st_state.parsed_summary == {"title": "退院時サマリ", "content": "詳細内容"}
            
            # モデル切り替えメッセージが表示されないことを確認
            mock_st_info.assert_not_called()
            
            # データベース保存が呼ばれることを確認
            mock_save.assert_called_once_with(result, session_params)

    @patch('streamlit.session_state', new_callable=MagicMock)
    def test_handle_success_result_model_switched_false(self, mock_st_state):
        """model_switchedがFalseの場合のテスト"""
        result = {
            "output_summary": "サマリ",
            "parsed_summary": {},
            "model_switched": False  # 明示的にFalse
        }
        session_params = {}
        
        with patch.object(StatisticsService, 'save_usage_to_database'), \
             patch('streamlit.info') as mock_st_info:
            
            StatisticsService.handle_success_result(result, session_params)
            
            # infoメッセージが表示されないことを確認
            mock_st_info.assert_not_called()

    @patch('streamlit.session_state', new_callable=MagicMock)
    def test_handle_success_result_no_model_switched_key(self, mock_st_state):
        """model_switchedキーがない場合のテスト"""
        result = {
            "output_summary": "サマリ",
            "parsed_summary": {}
            # model_switchedキーなし
        }
        session_params = {}
        
        with patch.object(StatisticsService, 'save_usage_to_database'), \
             patch('streamlit.info') as mock_st_info:
            
            StatisticsService.handle_success_result(result, session_params)
            
            # infoメッセージが表示されないことを確認
            mock_st_info.assert_not_called()

    @patch('services.statistics_service.get_usage_statistics_repository')
    @patch('services.statistics_service.datetime')
    def test_save_usage_to_database_repo_call_failure(self, mock_datetime, mock_get_repo):
        """リポジトリ取得失敗のテスト"""
        # リポジトリ取得で例外を発生
        mock_get_repo.side_effect = Exception("Repository initialization failed")
        
        result = {
            "model_detail": "test-model",
            "input_tokens": 10,
            "output_tokens": 20,
            "processing_time": 1.0
        }
        
        session_params = {
            "selected_document_type": "テスト",
            "selected_department": "テスト科",
            "selected_doctor": "テスト医師"
        }
        
        with patch('streamlit.warning') as mock_warning:
            # 例外が発生しても処理が継続されることを確認
            StatisticsService.save_usage_to_database(result, session_params)
            
            # 警告メッセージが表示されることを確認
            mock_warning.assert_called_once_with(
                "データベース保存中にエラーが発生しました: Repository initialization failed"
            )

    @patch('services.statistics_service.get_usage_statistics_repository')
    @patch('services.statistics_service.datetime')
    def test_save_usage_to_database_rounding_edge_cases(self, mock_datetime, mock_get_repo):
        """processing_time四捨五入の境界値テスト"""
        mock_repo = Mock()
        mock_get_repo.return_value = mock_repo
        
        fixed_time = datetime.datetime(2024, 1, 1, 0, 0, 0)
        mock_jst_time = fixed_time.replace(tzinfo=pytz.timezone('Asia/Tokyo'))
        mock_datetime.datetime.now.return_value.astimezone.return_value = mock_jst_time
        
        test_cases = [
            (4.4, 4),   # 四捨五入で4
            (4.5, 4),   # Python banker's rounding: round half to even
            (4.6, 5),   # 四捨五入で5
            (5.5, 6),   # Python banker's rounding: round half to even
            (0.4, 0),   # 四捨五入で0
            (0.5, 0),   # Python banker's rounding: round half to even
            (1.5, 2),   # Python banker's rounding: round half to even
        ]
        
        for processing_time, expected_rounded in test_cases:
            mock_repo.reset_mock()
            
            result = {
                "model_detail": "test-model",
                "input_tokens": 10,
                "output_tokens": 5,
                "processing_time": processing_time
            }
            
            session_params = {
                "selected_document_type": "テスト",
                "selected_department": "テスト科",
                "selected_doctor": "テスト医師"
            }
            
            StatisticsService.save_usage_to_database(result, session_params)
            
            # save_usageが呼ばれた引数を取得
            call_args = mock_repo.save_usage.call_args[0][0]
            assert call_args["processing_time"] == expected_rounded, \
                f"processing_time={processing_time} should round to {expected_rounded}, got {call_args['processing_time']}"