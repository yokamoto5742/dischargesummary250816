import pytest
from unittest.mock import Mock, patch

from services.model_service import ModelService
from utils.exceptions import APIError


class TestModelService:
    
    def test_determine_final_model_explicitly_selected(self):
        with patch('services.model_service.ModelService.get_model_from_prompt_if_needed') as mock_get_model, \
             patch('services.model_service.ModelService.check_model_switching_for_token_limit') as mock_check_switching:
            
            mock_get_model.return_value = "Claude"
            mock_check_switching.return_value = ("Claude", False, "Claude")
            
            result = ModelService.determine_final_model(
                "dept", "doc_type", "doctor", "Claude", True, "input", "info"
            )
            
            assert result == ("Claude", False, "Claude")
            mock_get_model.assert_called_once_with("dept", "doc_type", "doctor", "Claude", True)
            mock_check_switching.assert_called_once_with("Claude", "input", "info")

    def test_get_model_from_prompt_if_needed_explicitly_selected(self):
        result = ModelService.get_model_from_prompt_if_needed(
            "dept", "doc_type", "doctor", "Claude", True
        )
        
        assert result == "Claude"

    def test_get_model_from_prompt_if_needed_from_prompt(self):
        with patch('services.model_service.get_prompt_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.get_prompt.return_value = {"selected_model": "Gemini_Pro"}
            mock_get_manager.return_value = mock_manager
            
            result = ModelService.get_model_from_prompt_if_needed(
                "dept", "doc_type", "doctor", "Claude", False
            )
            
            assert result == "Gemini_Pro"
            mock_manager.get_prompt.assert_called_once_with("dept", "doc_type", "doctor")

    def test_get_model_from_prompt_if_needed_no_prompt_model(self):
        with patch('services.model_service.get_prompt_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.get_prompt.return_value = {"selected_model": None}
            mock_get_manager.return_value = mock_manager
            
            result = ModelService.get_model_from_prompt_if_needed(
                "dept", "doc_type", "doctor", "Claude", False
            )
            
            assert result == "Claude"

    def test_get_model_from_prompt_if_needed_no_prompt_data(self):
        with patch('services.model_service.get_prompt_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.get_prompt.return_value = None
            mock_get_manager.return_value = mock_manager
            
            result = ModelService.get_model_from_prompt_if_needed(
                "dept", "doc_type", "doctor", "Claude", False
            )
            
            assert result == "Claude"

    @patch('services.model_service.MAX_TOKEN_THRESHOLD', 1000)
    def test_check_model_switching_for_token_limit_no_switch_needed(self):
        input_text = "short text"
        additional_info = "short info"
        
        result = ModelService.check_model_switching_for_token_limit(
            "Claude", input_text, additional_info
        )
        
        assert result == ("Claude", False, "Claude")

    @patch('services.model_service.MAX_TOKEN_THRESHOLD', 10)
    @patch('services.model_service.GEMINI_CREDENTIALS', "fake_credentials")
    @patch('services.model_service.GEMINI_MODEL', "gemini-pro")
    def test_check_model_switching_for_token_limit_switch_to_gemini(self):
        input_text = "very long text that exceeds the token limit"
        additional_info = "additional information that makes it even longer"
        
        result = ModelService.check_model_switching_for_token_limit(
            "Claude", input_text, additional_info
        )
        
        assert result == ("Gemini_Pro", True, "Claude")

    @patch('services.model_service.MAX_TOKEN_THRESHOLD', 10)
    @patch('services.model_service.GEMINI_CREDENTIALS', None)
    def test_check_model_switching_for_token_limit_no_gemini_available(self):
        input_text = "very long text that exceeds the token limit"
        additional_info = "additional information"
        
        with pytest.raises(APIError) as exc_info:
            ModelService.check_model_switching_for_token_limit(
                "Claude", input_text, additional_info
            )
        
        # Check that the error message references token threshold
        assert "Gemini APIの認証情報が設定されていないため処理できません" in str(exc_info.value)

    @patch('services.model_service.MAX_TOKEN_THRESHOLD', 10)
    def test_check_model_switching_for_token_limit_non_claude_model(self):
        input_text = "very long text that exceeds the token limit"
        additional_info = "additional information"
        
        result = ModelService.check_model_switching_for_token_limit(
            "Gemini_Pro", input_text, additional_info
        )
        
        # Should not switch if not Claude model
        assert result == ("Gemini_Pro", False, "Gemini_Pro")

    def test_check_model_switching_for_token_limit_empty_additional_info(self):
        input_text = "some text"
        additional_info = None
        
        result = ModelService.check_model_switching_for_token_limit(
            "Claude", input_text, additional_info
        )
        
        # Should handle None additional_info gracefully
        assert result[0] == "Claude"
        assert result[1] is False

    @patch('services.model_service.CLAUDE_MODEL', "claude-3-sonnet")
    @patch('services.model_service.GEMINI_MODEL', "gemini-pro")
    @patch('services.model_service.GEMINI_FLASH_MODEL', "gemini-flash")
    def test_get_provider_and_model_all_options(self):
        test_cases = [
            ("Claude", ("claude", "claude-3-sonnet")),
            ("Gemini_Pro", ("gemini", "gemini-pro")),
            ("Gemini_Flash", ("gemini", "gemini-flash"))
        ]
        
        for selected_model, expected in test_cases:
            result = ModelService.get_provider_and_model(selected_model)
            assert result == expected

    def test_get_provider_and_model_invalid_model(self):
        with pytest.raises(APIError):
            ModelService.get_provider_and_model("InvalidModel")

    def test_normalize_selection_params_valid_values(self):
        with patch('services.model_service.DEFAULT_DEPARTMENT', ["dept1", "dept2"]), \
             patch('services.model_service.DOCUMENT_TYPES', ["type1", "type2"]):
            
            result = ModelService.normalize_selection_params("dept1", "type1")
            
            assert result == ("dept1", "type1")

    def test_normalize_selection_params_invalid_department(self):
        with patch('services.model_service.DEFAULT_DEPARTMENT', ["dept1", "dept2"]), \
             patch('services.model_service.DOCUMENT_TYPES', ["type1", "type2"]):
            
            result = ModelService.normalize_selection_params("invalid_dept", "type1")
            
            assert result == ("default", "type1")

    def test_normalize_selection_params_invalid_document_type(self):
        with patch('services.model_service.DEFAULT_DEPARTMENT', ["dept1", "dept2"]), \
             patch('services.model_service.DOCUMENT_TYPES', ["type1", "type2"]):
            
            result = ModelService.normalize_selection_params("dept1", "invalid_type")
            
            assert result == ("dept1", "type1")  # First item in DOCUMENT_TYPES

    def test_normalize_selection_params_both_invalid(self):
        with patch('services.model_service.DEFAULT_DEPARTMENT', ["dept1", "dept2"]), \
             patch('services.model_service.DOCUMENT_TYPES', ["type1", "type2"]):
            
            result = ModelService.normalize_selection_params("invalid_dept", "invalid_type")
            
            assert result == ("default", "type1")