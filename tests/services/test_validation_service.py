from unittest.mock import patch

import pytest

from services.validation_service import ValidationService
from utils.exceptions import APIError


class TestValidationService:
    
    @patch('services.validation_service.GEMINI_CREDENTIALS', "fake_credentials")
    @patch('services.validation_service.CLAUDE_AVAILABLE', True)
    def test_validate_api_credentials_success(self):
        # Should not raise any exception when both credentials are available
        ValidationService.validate_api_credentials()

    @patch('services.validation_service.GEMINI_CREDENTIALS', "fake_credentials")
    @patch('services.validation_service.CLAUDE_AVAILABLE', False)
    def test_validate_api_credentials_only_gemini(self):
        # Should not raise exception when at least one credential is available
        ValidationService.validate_api_credentials()

    @patch('services.validation_service.GEMINI_CREDENTIALS', None)
    @patch('services.validation_service.CLAUDE_AVAILABLE', True)
    def test_validate_api_credentials_only_claude(self):
        # Should not raise exception when at least one credential is available
        ValidationService.validate_api_credentials()

    @patch('services.validation_service.GEMINI_CREDENTIALS', None)
    @patch('services.validation_service.CLAUDE_AVAILABLE', False)
    def test_validate_api_credentials_no_credentials(self):
        with pytest.raises(APIError):
            ValidationService.validate_api_credentials()

    @patch('services.validation_service.st')
    def test_validate_input_text_empty_text(self, mock_st):
        ValidationService.validate_input_text("")
        mock_st.warning.assert_called_once()

    @patch('services.validation_service.st')
    def test_validate_input_text_none_text(self, mock_st):
        ValidationService.validate_input_text(None)
        mock_st.warning.assert_called_once()

    @patch('services.validation_service.MIN_INPUT_TOKENS', 10)
    @patch('services.validation_service.st')
    def test_validate_input_text_too_short(self, mock_st):
        ValidationService.validate_input_text("short")
        mock_st.warning.assert_called_once()

    @patch('services.validation_service.MAX_INPUT_TOKENS', 50)
    @patch('services.validation_service.st')
    def test_validate_input_text_too_long(self, mock_st):
        long_text = "x" * 100
        ValidationService.validate_input_text(long_text)
        mock_st.warning.assert_called_once()

    @patch('services.validation_service.MIN_INPUT_TOKENS', 5)
    @patch('services.validation_service.MAX_INPUT_TOKENS', 100)
    @patch('services.validation_service.st')
    def test_validate_input_text_valid_length(self, mock_st):
        ValidationService.validate_input_text("This is a valid text")
        mock_st.warning.assert_not_called()

    @patch('services.validation_service.GEMINI_CREDENTIALS', "fake_credentials")
    @patch('services.validation_service.CLAUDE_AVAILABLE', True)
    @patch('services.validation_service.MIN_INPUT_TOKENS', 5)
    @patch('services.validation_service.MAX_INPUT_TOKENS', 100)
    @patch('services.validation_service.st')
    def test_validate_inputs_all_valid(self, mock_st):
        # Should not raise exception when all validations pass
        ValidationService.validate_inputs("This is a valid text")
        mock_st.warning.assert_not_called()

    @patch('services.validation_service.GEMINI_CREDENTIALS', None)
    @patch('services.validation_service.CLAUDE_AVAILABLE', False)
    def test_validate_inputs_no_credentials(self):
        with pytest.raises(APIError):
            ValidationService.validate_inputs("This is a valid text")

    @patch('services.validation_service.GEMINI_CREDENTIALS', "fake_credentials")
    def test_validate_api_credentials_for_provider_gemini_success(self):
        # Should not raise exception when Gemini credentials are available
        ValidationService.validate_api_credentials_for_provider("gemini")

    @patch('services.validation_service.GEMINI_CREDENTIALS', None)
    def test_validate_api_credentials_for_provider_gemini_failure(self):
        with pytest.raises(APIError):
            ValidationService.validate_api_credentials_for_provider("gemini")

    @patch('services.validation_service.CLAUDE_AVAILABLE', True)
    def test_validate_api_credentials_for_provider_claude_success(self):
        # Should not raise exception when Claude is available
        ValidationService.validate_api_credentials_for_provider("claude")

    @patch('services.validation_service.CLAUDE_AVAILABLE', False)
    def test_validate_api_credentials_for_provider_claude_failure(self):
        with pytest.raises(APIError):
            ValidationService.validate_api_credentials_for_provider("claude")

    def test_validate_api_credentials_for_provider_invalid_provider(self):
        with pytest.raises(APIError):
            ValidationService.validate_api_credentials_for_provider("invalid_provider")