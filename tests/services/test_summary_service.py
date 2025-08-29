import pytest
import datetime
from unittest.mock import Mock, patch, MagicMock
from services.summary_service import SummaryService
from utils.exceptions import APIError


class TestSummaryService:

    def test_process_summary_success(self):
        """正常なサマリ処理のテスト"""
        mock_input_text = "患者の診療記録"
        mock_additional_info = "追加情報"
        mock_current_prescription = "処方情報"
        
        with patch('services.summary_service.ValidationService.validate_inputs'), \
             patch.object(SummaryService, 'get_session_parameters') as mock_get_params, \
             patch.object(SummaryService, 'execute_summary_generation') as mock_execute, \
             patch.object(SummaryService, 'handle_generation_result') as mock_handle:
            
            mock_get_params.return_value = {
                "available_models": ["claude", "gemini"],
                "selected_model": "claude",
                "selected_department": "内科",
                "selected_document_type": "退院時サマリ",
                "selected_doctor": "田中医師",
                "model_explicitly_selected": True
            }
            
            mock_result = {
                "success": True,
                "summary": "生成されたサマリ",
                "processing_time": 5.2
            }
            mock_execute.return_value = mock_result
            
            SummaryService.process_summary(
                mock_input_text, 
                mock_additional_info, 
                mock_current_prescription
            )
            
            mock_execute.assert_called_once_with(
                mock_input_text, 
                mock_additional_info, 
                mock_current_prescription, 
                mock_get_params.return_value
            )
            mock_handle.assert_called_once_with(
                mock_result, 
                mock_get_params.return_value
            )

    def test_process_summary_validation_error(self):
        """入力検証エラーのテスト"""
        with patch('services.summary_service.ValidationService.validate_inputs', 
                  side_effect=ValueError("入力が無効です")), \
             patch('streamlit.error') as mock_st_error:
            
            result = SummaryService.process_summary("")
            
            # @handle_error decorator catches the exception and shows streamlit error
            assert result is None
            mock_st_error.assert_called_once_with("予期しないエラー: 入力が無効です")

    def test_get_session_parameters_default_values(self):
        """セッションパラメータのデフォルト値テスト"""
        with patch('streamlit.session_state', new_callable=MagicMock) as mock_st:
            mock_st.available_models = []
            mock_st.selected_model = None
            mock_st.selected_department = "default"
            mock_st.selected_document_type = "退院時サマリ"
            mock_st.selected_doctor = "default"
            mock_st.model_explicitly_selected = False
            
            result = SummaryService.get_session_parameters()
            
            expected = {
                "available_models": [],
                "selected_model": None,
                "selected_department": "default",
                "selected_document_type": "退院時サマリ",
                "selected_doctor": "default",
                "model_explicitly_selected": False
            }
            
            assert result == expected

    def test_get_session_parameters_with_values(self):
        """セッションパラメータの値設定テスト"""
        with patch('streamlit.session_state', new_callable=MagicMock) as mock_st:
            mock_st.available_models = ["claude", "gemini"]
            mock_st.selected_model = "claude"
            mock_st.selected_department = "内科"
            mock_st.selected_document_type = "入院記録"
            mock_st.selected_doctor = "佐藤医師"
            mock_st.model_explicitly_selected = True
            
            result = SummaryService.get_session_parameters()
            
            expected = {
                "available_models": ["claude", "gemini"],
                "selected_model": "claude",
                "selected_department": "内科",
                "selected_document_type": "入院記録",
                "selected_doctor": "佐藤医師",
                "model_explicitly_selected": True
            }
            
            assert result == expected

    def test_execute_summary_generation_success(self):
        """サマリ生成成功のテスト"""
        mock_input_text = "患者記録"
        mock_additional_info = "追加情報"
        mock_current_prescription = "処方"
        mock_session_params = {
            "selected_model": "claude",
            "selected_department": "内科"
        }
        
        mock_result = {
            "success": True,
            "summary": "生成されたサマリ",
            "processing_time": 3.5
        }
        
        with patch.object(SummaryService, 'execute_summary_generation_with_ui', 
                         return_value=mock_result) as mock_execute_ui:
            
            result = SummaryService.execute_summary_generation(
                mock_input_text,
                mock_additional_info,
                mock_current_prescription,
                mock_session_params
            )
            
            assert result == mock_result
            mock_execute_ui.assert_called_once_with(
                mock_input_text,
                mock_additional_info,
                mock_current_prescription,
                mock_session_params
            )

    def test_execute_summary_generation_failure(self):
        """サマリ生成失敗のテスト"""
        mock_input_text = "患者記録"
        mock_additional_info = "追加情報"
        mock_current_prescription = "処方"
        mock_session_params = {"selected_model": "claude"}
        
        mock_result = {
            "success": False,
            "error": "API呼び出しに失敗しました"
        }
        
        with patch.object(SummaryService, 'execute_summary_generation_with_ui', 
                         return_value=mock_result):
            
            with pytest.raises(APIError, match="API呼び出しに失敗しました"):
                SummaryService.execute_summary_generation(
                    mock_input_text,
                    mock_additional_info,
                    mock_current_prescription,
                    mock_session_params
                )

    def test_execute_summary_generation_exception(self):
        """サマリ生成時の例外処理テスト"""
        mock_input_text = "患者記録"
        mock_additional_info = "追加情報"
        mock_current_prescription = "処方"
        mock_session_params = {"selected_model": "claude"}
        
        with patch.object(SummaryService, 'execute_summary_generation_with_ui', 
                         side_effect=Exception("予期しないエラー")):
            
            with pytest.raises(APIError, match="作成中にエラーが発生しました: 予期しないエラー"):
                SummaryService.execute_summary_generation(
                    mock_input_text,
                    mock_additional_info,
                    mock_current_prescription,
                    mock_session_params
                )

    @patch('streamlit.empty')
    @patch('queue.Queue')
    @patch('threading.Thread')
    @patch('datetime.datetime')
    def test_execute_summary_generation_with_ui(self, mock_datetime, mock_thread_class, 
                                               mock_queue_class, mock_st_empty):
        """UI付きサマリ生成のテスト"""
        mock_start_time = datetime.datetime(2024, 1, 1, 12, 0, 0)
        mock_end_time = datetime.datetime(2024, 1, 1, 12, 0, 5)
        mock_datetime.now.side_effect = [mock_start_time, mock_end_time]
        
        # total_seconds()の戻り値をモック
        mock_timedelta = Mock()
        mock_timedelta.total_seconds.return_value = 5.0
        mock_datetime.__sub__ = Mock(return_value=mock_timedelta)
        mock_end_time.__sub__ = Mock(return_value=mock_timedelta)
        
        mock_queue = Mock()
        mock_result = {
            "success": True,
            "summary": "生成されたサマリ",
            "model_used": "claude"
        }
        mock_queue.get.return_value = mock_result
        mock_queue_class.return_value = mock_queue
        
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread
        
        mock_placeholder = Mock()
        mock_st_empty.return_value = mock_placeholder
        
        session_params = {
            "selected_department": "内科",
            "selected_model": "claude",
            "selected_document_type": "退院時サマリ",
            "selected_doctor": "田中医師",
            "model_explicitly_selected": True
        }
        
        with patch('services.generation_service.GenerationService.display_progress_with_timer'), \
             patch('streamlit.session_state', new_callable=MagicMock) as mock_st_state:
            
            result = SummaryService.execute_summary_generation_with_ui(
                "患者記録",
                "追加情報",
                "処方情報",
                session_params
            )
            
            # スレッドが正しく作成されたかチェック
            mock_thread_class.assert_called_once()
            mock_thread.start.assert_called_once()
            mock_thread.join.assert_called_once()
            
            # 結果が正しく処理されたかチェック
            expected_result = {
                "success": True,
                "summary": "生成されたサマリ",
                "model_used": "claude",
                "processing_time": 5.0
            }
            assert result == expected_result
            
            # セッション状態が更新されたかチェック
            assert mock_st_state.summary_generation_time == 5.0

    @patch('services.statistics_service.StatisticsService.handle_success_result')
    def test_handle_generation_result(self, mock_handle_success):
        """生成結果処理のテスト"""
        mock_result = {
            "success": True,
            "summary": "生成されたサマリ",
            "processing_time": 3.5
        }
        
        mock_session_params = {
            "selected_model": "claude",
            "selected_department": "内科"
        }
        
        SummaryService.handle_generation_result(mock_result, mock_session_params)
        
        mock_handle_success.assert_called_once_with(mock_result, mock_session_params)

    def test_integration_process_summary_full_flow(self):
        """統合テスト - プロセス全体の流れ"""
        mock_input_text = "患者の詳細な診療記録"
        
        mock_session_params = {
            "available_models": ["claude", "gemini"],
            "selected_model": "claude",
            "selected_department": "外科",
            "selected_document_type": "退院時サマリ",
            "selected_doctor": "山田医師",
            "model_explicitly_selected": False
        }
        
        mock_result = {
            "success": True,
            "summary": "統合テスト用のサマリ",
            "processing_time": 4.2,
            "model_used": "claude",
            "tokens_used": 150
        }
        
        with patch('services.summary_service.ValidationService.validate_inputs'), \
             patch.object(SummaryService, 'get_session_parameters', 
                         return_value=mock_session_params), \
             patch.object(SummaryService, 'execute_summary_generation', 
                         return_value=mock_result) as mock_execute, \
             patch.object(SummaryService, 'handle_generation_result') as mock_handle:
            
            SummaryService.process_summary(mock_input_text)
            
            # すべてのステップが正しい順序で呼ばれたかチェック
            mock_execute.assert_called_once_with(
                mock_input_text, "", "", mock_session_params
            )
            mock_handle.assert_called_once_with(mock_result, mock_session_params)