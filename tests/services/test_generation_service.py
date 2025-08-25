import queue
import threading
import pytest
from unittest.mock import Mock, patch, MagicMock
import datetime

from services.generation_service import GenerationService
from utils.exceptions import APIError


class TestGenerationService:
    
    def test_prepare_generation_parameters(self):
        with patch('services.generation_service.ModelService.normalize_selection_params') as mock_normalize, \
             patch('services.generation_service.ModelService.determine_final_model') as mock_determine, \
             patch('services.generation_service.ModelService.get_provider_and_model') as mock_get_provider, \
             patch('services.generation_service.ValidationService.validate_api_credentials_for_provider') as mock_validate:
            
            mock_normalize.return_value = ("normalized_dept", "normalized_doc_type")
            mock_determine.return_value = ("final_model", True, "original_model")
            mock_get_provider.return_value = ("gemini", "gemini-pro")
            
            result = GenerationService.prepare_generation_parameters(
                "dept", "doc_type", "doctor", "model", True, "input", "info"
            )
            
            expected = {
                'normalized_dept': "normalized_dept",
                'normalized_doc_type': "normalized_doc_type",
                'provider': "gemini",
                'model_name': "gemini-pro",
                'model_detail': "gemini-pro",
                'model_switched': True,
                'original_model': "original_model"
            }
            
            assert result == expected
            mock_normalize.assert_called_once_with("dept", "doc_type")
            mock_determine.assert_called_once_with(
                "normalized_dept", "normalized_doc_type", "doctor", 
                "model", True, "input", "info"
            )
            mock_get_provider.assert_called_once_with("final_model")
            mock_validate.assert_called_once_with("gemini")

    def test_prepare_generation_parameters_claude_provider(self):
        with patch('services.generation_service.ModelService.normalize_selection_params') as mock_normalize, \
             patch('services.generation_service.ModelService.determine_final_model') as mock_determine, \
             patch('services.generation_service.ModelService.get_provider_and_model') as mock_get_provider, \
             patch('services.generation_service.ValidationService.validate_api_credentials_for_provider') as mock_validate:
            
            mock_normalize.return_value = ("normalized_dept", "normalized_doc_type")
            mock_determine.return_value = ("Claude", False, "Claude")
            mock_get_provider.return_value = ("claude", "claude-3-sonnet")
            
            result = GenerationService.prepare_generation_parameters(
                "dept", "doc_type", "doctor", "model", False, "input", "info"
            )
            
            assert result['model_detail'] == "Claude"  # For Claude, use final_model not model_name

    def test_execute_api_generation(self):
        with patch('services.generation_service.generate_summary') as mock_generate:
            mock_generate.return_value = ("summary", 100, 200)
            
            result = GenerationService.execute_api_generation(
                "gemini", "gemini-pro", "input", "info", "prescription",
                "dept", "doc_type", "doctor"
            )
            
            expected = {
                'output_summary': "summary",
                'input_tokens': 100,
                'output_tokens': 200
            }
            
            assert result == expected
            mock_generate.assert_called_once_with(
                provider="gemini",
                medical_text="input",
                additional_info="info",
                current_prescription="prescription",
                department="dept",
                document_type="doc_type",
                doctor="doctor",
                model_name="gemini-pro"
            )

    def test_format_generation_result(self):
        with patch('services.generation_service.format_output_summary') as mock_format, \
             patch('services.generation_service.parse_output_summary') as mock_parse:
            
            mock_format.return_value = "formatted_summary"
            mock_parse.return_value = {"parsed": "summary"}
            
            result = GenerationService.format_generation_result(
                "raw_summary", 100, 200, "gemini-pro", True, "Claude"
            )
            
            expected = {
                "success": True,
                "output_summary": "formatted_summary",
                "parsed_summary": {"parsed": "summary"},
                "input_tokens": 100,
                "output_tokens": 200,
                "model_detail": "gemini-pro",
                "model_switched": True,
                "original_model": "Claude"
            }
            
            assert result == expected
            mock_format.assert_called_once_with("raw_summary")
            mock_parse.assert_called_once_with("formatted_summary")

    def test_format_generation_result_no_model_switch(self):
        with patch('services.generation_service.format_output_summary') as mock_format, \
             patch('services.generation_service.parse_output_summary') as mock_parse:
            
            mock_format.return_value = "formatted_summary"
            mock_parse.return_value = {"parsed": "summary"}
            
            result = GenerationService.format_generation_result(
                "raw_summary", 100, 200, "gemini-pro", False, "gemini-pro"
            )
            
            assert result["model_switched"] is False
            assert result["original_model"] is None

    def test_generate_summary_task_success(self):
        mock_queue = Mock(spec=queue.Queue)
        
        with patch('services.generation_service.GenerationService.prepare_generation_parameters') as mock_prepare, \
             patch('services.generation_service.GenerationService.execute_api_generation') as mock_execute, \
             patch('services.generation_service.GenerationService.format_generation_result') as mock_format:
            
            mock_prepare.return_value = {
                'provider': 'gemini',
                'model_name': 'gemini-pro',
                'normalized_dept': 'dept',
                'normalized_doc_type': 'doc_type',
                'model_detail': 'gemini-pro',
                'model_switched': False,
                'original_model': 'gemini-pro'
            }
            
            mock_execute.return_value = {
                'output_summary': 'summary',
                'input_tokens': 100,
                'output_tokens': 200
            }
            
            mock_format.return_value = {
                'success': True,
                'output_summary': 'formatted',
                'input_tokens': 100,
                'output_tokens': 200
            }
            
            GenerationService.generate_summary_task(
                "input_text", "dept", "model", mock_queue,
                additional_info="info", current_prescription="prescription",
                selected_document_type="doc_type", selected_doctor="doctor",
                model_explicitly_selected=True
            )
            
            mock_queue.put.assert_called_once()
            result_call = mock_queue.put.call_args[0][0]
            assert result_call['success'] is True

    def test_generate_summary_task_exception(self):
        mock_queue = Mock(spec=queue.Queue)
        
        with patch('services.generation_service.GenerationService.prepare_generation_parameters') as mock_prepare:
            mock_prepare.side_effect = Exception("Test error")
            
            GenerationService.generate_summary_task(
                "input_text", "dept", "model", mock_queue
            )
            
            mock_queue.put.assert_called_once()
            result_call = mock_queue.put.call_args[0][0]
            assert result_call['success'] is False
            assert "Test error" in result_call['error']

    @patch('services.generation_service.time.sleep')
    @patch('services.generation_service.datetime')
    @patch('services.generation_service.st')
    def test_display_progress_with_timer(self, mock_st, mock_datetime, mock_sleep):
        mock_thread = Mock(spec=threading.Thread)
        mock_placeholder = Mock()
        start_time = datetime.datetime.now()
        
        # Mock datetime for elapsed time calculation
        mock_datetime.datetime.now.side_effect = [
            start_time + datetime.timedelta(seconds=1),
            start_time + datetime.timedelta(seconds=2),
            start_time + datetime.timedelta(seconds=3)
        ]
        
        # Thread becomes not alive after 2 iterations
        mock_thread.is_alive.side_effect = [True, True, False]
        
        # Mock context manager for spinner
        mock_spinner = Mock()
        mock_st.spinner.return_value.__enter__ = Mock(return_value=mock_spinner)
        mock_st.spinner.return_value.__exit__ = Mock(return_value=None)
        
        GenerationService.display_progress_with_timer(
            mock_thread, mock_placeholder, start_time
        )
        
        # Check that placeholder.text was called with elapsed time
        assert mock_placeholder.text.call_count >= 2
        mock_sleep.assert_called()

    @patch('services.generation_service.time.sleep')
    @patch('services.generation_service.datetime')
    @patch('services.generation_service.st')
    def test_display_progress_with_timer_immediate_finish(self, mock_st, mock_datetime, mock_sleep):
        mock_thread = Mock(spec=threading.Thread)
        mock_placeholder = Mock()
        start_time = datetime.datetime.now()
        
        # Thread is not alive from the start
        mock_thread.is_alive.return_value = False
        
        # Mock context manager for spinner
        mock_spinner = Mock()
        mock_st.spinner.return_value.__enter__ = Mock(return_value=mock_spinner)
        mock_st.spinner.return_value.__exit__ = Mock(return_value=None)
        
        GenerationService.display_progress_with_timer(
            mock_thread, mock_placeholder, start_time
        )
        
        # Should have been called at least once with initial 0 seconds
        mock_placeholder.text.assert_called()