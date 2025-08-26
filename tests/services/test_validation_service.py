from unittest.mock import patch

import pytest

from services.validation_service import ValidationService
from utils.exceptions import APIError


class TestValidationService:
    
    @patch('services.validation_service.GEMINI_CREDENTIALS', "fake_credentials")
    @patch('services.validation_service.CLAUDE_API_KEY', "fake_key")
    def test_validate_api_credentials_success(self):
        # Should not raise any exception when both credentials are available
        ValidationService.validate_api_credentials()

    @patch('services.validation_service.GEMINI_CREDENTIALS', "fake_credentials")
    @patch('services.validation_service.CLAUDE_API_KEY', None)
    def test_validate_api_credentials_only_gemini(self):
        # Should not raise exception when at least one credential is available
        ValidationService.validate_api_credentials()

    @patch('services.validation_service.GEMINI_CREDENTIALS', None)
    @patch('services.validation_service.CLAUDE_API_KEY', "fake_key")
    def test_validate_api_credentials_only_claude(self):
        # Should not raise exception when at least one credential is available
        ValidationService.validate_api_credentials()

    @patch('services.validation_service.GEMINI_CREDENTIALS', None)
    @patch('services.validation_service.CLAUDE_API_KEY', None)
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

    @patch('services.validation_service.MAX_INPUT_TOKENS', 10)
    @patch('services.validation_service.st')
    def test_validate_input_text_too_long(self, mock_st):
        ValidationService.validate_input_text("this text is too long for the limit")
        mock_st.warning.assert_called_once()

    @patch('services.validation_service.MIN_INPUT_TOKENS', 5)
    @patch('services.validation_service.MAX_INPUT_TOKENS', 50)
    @patch('services.validation_service.st')
    def test_validate_input_text_valid_length(self, mock_st):
        ValidationService.validate_input_text("this is a valid length text")
        mock_st.warning.assert_not_called()

    @patch('services.validation_service.MIN_INPUT_TOKENS', 5)
    @patch('services.validation_service.MAX_INPUT_TOKENS', 50)
    @patch('services.validation_service.st')
    def test_validate_input_text_with_whitespace(self, mock_st):
        ValidationService.validate_input_text("   valid text   ")
        mock_st.warning.assert_not_called()

    @patch('services.validation_service.ValidationService.validate_api_credentials')
    @patch('services.validation_service.ValidationService.validate_input_text')
    def test_validate_inputs(self, mock_validate_input_text, mock_validate_api_credentials):
        ValidationService.validate_inputs("test input")
        
        mock_validate_api_credentials.assert_called_once()
        mock_validate_input_text.assert_called_once_with("test input")

    @patch('services.validation_service.CLAUDE_API_KEY', "fake_key")
    def test_validate_api_credentials_for_provider_claude_valid(self):
        # Should not raise exception when Claude credentials are valid
        ValidationService.validate_api_credentials_for_provider("claude")

    @patch('services.validation_service.CLAUDE_API_KEY', None)
    def test_validate_api_credentials_for_provider_claude_invalid(self):
        with pytest.raises(APIError):
            ValidationService.validate_api_credentials_for_provider("claude")

    @patch('services.validation_service.GEMINI_CREDENTIALS', "fake_credentials")
    def test_validate_api_credentials_for_provider_gemini_valid(self):
        # Should not raise exception when Gemini credentials are valid
        ValidationService.validate_api_credentials_for_provider("gemini")

    @patch('services.validation_service.GEMINI_CREDENTIALS', None)
    def test_validate_api_credentials_for_provider_gemini_invalid(self):
        with pytest.raises(APIError):
            ValidationService.validate_api_credentials_for_provider("gemini")

    def test_validate_api_credentials_for_provider_invalid_provider(self):
        with pytest.raises(APIError):
            ValidationService.validate_api_credentials_for_provider("invalid_provider")

    @patch('services.validation_service.CLAUDE_API_KEY', "fake_key")
    @patch('services.validation_service.GEMINI_CREDENTIALS', "fake_credentials")
    def test_validate_api_credentials_for_provider_all_providers(self):
        # Test all valid providers
        providers = ["claude", "gemini"]
        
        for provider in providers:
            # Should not raise exception for valid providers
            ValidationService.validate_api_credentials_for_provider(provider)

    @patch('services.validation_service.CLAUDE_API_KEY', "")  # Empty string should be falsy
    def test_validate_api_credentials_for_provider_empty_string_key(self):
        with pytest.raises(APIError):
            ValidationService.validate_api_credentials_for_provider("claude")

    @patch('services.validation_service.GEMINI_CREDENTIALS', "")  # Empty string should be falsy
    def test_validate_api_credentials_for_provider_empty_string_credentials(self):
        with pytest.raises(APIError):
            ValidationService.validate_api_credentials_for_provider("gemini")

    @patch('services.validation_service.CLAUDE_API_KEY', False)
    def test_validate_api_credentials_for_provider_false_key(self):
        with pytest.raises(APIError):
            ValidationService.validate_api_credentials_for_provider("claude")

    def test_validate_api_credentials_for_provider_case_sensitivity(self):
        # Test that provider name is case sensitive (should fail for uppercase)
        with pytest.raises(APIError):
            ValidationService.validate_api_credentials_for_provider("CLAUDE")
        
        with pytest.raises(APIError):
            ValidationService.validate_api_credentials_for_provider("GEMINI")