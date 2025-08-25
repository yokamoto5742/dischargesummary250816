import pytest
from unittest.mock import Mock, patch

from external_service.gemini_api import GeminiAPIClient
from utils.exceptions import APIError


class TestGeminiAPIClient:
    
    def setup_method(self):
        with patch('external_service.gemini_api.GEMINI_CREDENTIALS', 'fake_credentials'), \
             patch('external_service.gemini_api.GEMINI_MODEL', 'gemini-pro'):
            self.client = GeminiAPIClient()

    def test_init(self):
        with patch('external_service.gemini_api.GEMINI_CREDENTIALS', 'test_credentials'), \
             patch('external_service.gemini_api.GEMINI_MODEL', 'test_model'):
            client = GeminiAPIClient()
            assert client.api_key == 'test_credentials'
            assert client.default_model == 'test_model'
            assert client.client is None

    @patch('external_service.gemini_api.genai')
    def test_initialize_success(self, mock_genai):
        mock_client_instance = Mock()
        mock_genai.Client.return_value = mock_client_instance
        
        result = self.client.initialize()
        
        assert result is True
        assert self.client.client is mock_client_instance
        mock_genai.Client.assert_called_once_with(api_key='fake_credentials')

    def test_initialize_no_api_key(self):
        client = GeminiAPIClient()
        client.api_key = None
        
        with pytest.raises(APIError) as exc_info:
            client.initialize()
        assert "API_CREDENTIALS_MISSING" in str(exc_info.value) or "APIキー" in str(exc_info.value)

    @patch('external_service.gemini_api.genai')
    def test_initialize_genai_exception(self, mock_genai):
        mock_genai.Client.side_effect = Exception("Connection error")
        
        with pytest.raises(APIError) as exc_info:
            self.client.initialize()
        assert "Gemini API初期化エラー" in str(exc_info.value)

    @patch('external_service.gemini_api.GEMINI_THINKING_BUDGET', None)
    def test_generate_content_without_thinking_budget(self):
        mock_response = Mock()
        mock_response.text = "Generated summary text"
        mock_usage = Mock()
        mock_usage.prompt_token_count = 150
        mock_usage.candidates_token_count = 300
        mock_response.usage_metadata = mock_usage
        
        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        self.client.client = mock_client
        
        result = self.client._generate_content("Test prompt", "gemini-pro")
        
        assert result == ("Generated summary text", 150, 300)
        mock_client.models.generate_content.assert_called_once_with(
            model="gemini-pro",
            contents="Test prompt"
        )

    @patch('external_service.gemini_api.GEMINI_THINKING_BUDGET', 1000)
    @patch('external_service.gemini_api.types')
    def test_generate_content_with_thinking_budget(self, mock_types):
        mock_thinking_config = Mock()
        mock_types.ThinkingConfig.return_value = mock_thinking_config
        mock_generate_config = Mock()
        mock_types.GenerateContentConfig.return_value = mock_generate_config
        
        mock_response = Mock()
        mock_response.text = "Generated summary text"
        mock_usage = Mock()
        mock_usage.prompt_token_count = 150
        mock_usage.candidates_token_count = 300
        mock_response.usage_metadata = mock_usage
        
        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        self.client.client = mock_client
        
        result = self.client._generate_content("Test prompt", "gemini-pro")
        
        assert result == ("Generated summary text", 150, 300)
        mock_types.ThinkingConfig.assert_called_once_with(thinking_budget=1000)
        mock_types.GenerateContentConfig.assert_called_once_with(
            thinking_config=mock_thinking_config
        )
        mock_client.models.generate_content.assert_called_once_with(
            model="gemini-pro",
            contents="Test prompt",
            config=mock_generate_config
        )

    def test_generate_content_no_text_attribute(self):
        mock_response = Mock()
        delattr(mock_response, 'text')  # Remove text attribute
        mock_response.__str__ = Mock(return_value="String representation of response")
        
        mock_usage = Mock()
        mock_usage.prompt_token_count = 150
        mock_usage.candidates_token_count = 300
        mock_response.usage_metadata = mock_usage
        
        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        self.client.client = mock_client
        
        result = self.client._generate_content("Test prompt", "gemini-pro")
        
        assert result == ("String representation of response", 150, 300)

    def test_generate_content_no_usage_metadata(self):
        mock_response = Mock()
        mock_response.text = "Generated text"
        delattr(mock_response, 'usage_metadata')  # Remove usage_metadata attribute
        
        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        self.client.client = mock_client
        
        result = self.client._generate_content("Test prompt", "gemini-pro")
        
        assert result == ("Generated text", 0, 0)  # Default token counts

    def test_generate_content_partial_usage_metadata(self):
        mock_response = Mock()
        mock_response.text = "Generated text"
        mock_usage = Mock()
        mock_usage.prompt_token_count = 100
        # Missing candidates_token_count
        delattr(mock_usage, 'candidates_token_count')
        mock_response.usage_metadata = mock_usage
        
        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        self.client.client = mock_client
        
        result = self.client._generate_content("Test prompt", "gemini-pro")
        
        # Should handle missing candidates_token_count gracefully
        assert result[0] == "Generated text"
        assert result[1] == 100  # input_tokens should be available
        assert result[2] == 0    # output_tokens should default to 0

    def test_generate_content_api_exception(self):
        mock_client = Mock()
        mock_client.models.generate_content.side_effect = Exception("API call failed")
        self.client.client = mock_client
        
        with pytest.raises(Exception) as exc_info:
            self.client._generate_content("Test prompt", "gemini-pro")
        assert "API call failed" in str(exc_info.value)

    @patch('external_service.gemini_api.genai')
    def test_integration_initialize_and_generate(self, mock_genai):
        # Integration test for initialize and generate_content
        mock_response = Mock()
        mock_response.text = "Integration test response"
        mock_usage = Mock()
        mock_usage.prompt_token_count = 50
        mock_usage.candidates_token_count = 100
        mock_response.usage_metadata = mock_usage
        
        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        
        # Initialize the client
        result_init = self.client.initialize()
        assert result_init is True
        
        # Generate content
        result_generate = self.client._generate_content("Test prompt", "gemini-pro")
        assert result_generate == ("Integration test response", 50, 100)

    def test_generate_content_empty_response_text(self):
        mock_response = Mock()
        mock_response.text = ""  # Empty text
        mock_usage = Mock()
        mock_usage.prompt_token_count = 50
        mock_usage.candidates_token_count = 0
        mock_response.usage_metadata = mock_usage
        
        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        self.client.client = mock_client
        
        result = self.client._generate_content("Test prompt", "gemini-pro")
        
        assert result == ("", 50, 0)

    def test_generate_content_complex_prompt(self):
        mock_response = Mock()
        mock_response.text = "Complex response"
        mock_usage = Mock()
        mock_usage.prompt_token_count = 200
        mock_usage.candidates_token_count = 400
        mock_response.usage_metadata = mock_usage
        
        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        self.client.client = mock_client
        
        complex_prompt = "Test prompt with Japanese: 日本語のテスト\nMultiple lines\nSpecial chars: @#$%"
        result = self.client._generate_content(complex_prompt, "gemini-pro")
        
        assert result == ("Complex response", 200, 400)
        mock_client.models.generate_content.assert_called_once_with(
            model="gemini-pro",
            contents=complex_prompt
        )

    @patch('external_service.gemini_api.GEMINI_THINKING_BUDGET', 500)
    @patch('external_service.gemini_api.types')
    def test_generate_content_thinking_config_creation(self, mock_types):
        mock_response = Mock()
        mock_response.text = "Test response"
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 100
        mock_response.usage_metadata.candidates_token_count = 200
        
        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        self.client.client = mock_client
        
        self.client._generate_content("Test prompt", "gemini-pro")
        
        # Verify that ThinkingConfig is created with correct budget
        mock_types.ThinkingConfig.assert_called_once_with(thinking_budget=500)
        mock_types.GenerateContentConfig.assert_called_once()

    def test_generate_content_str_conversion(self):
        # Test when response doesn't have text but can be converted to string
        mock_response = Mock()
        delattr(mock_response, 'text')
        mock_response.__str__ = Mock(return_value="Mock string conversion")
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 75
        mock_response.usage_metadata.candidates_token_count = 150
        
        mock_client = Mock()
        mock_client.models.generate_content.return_value = mock_response
        self.client.client = mock_client
        
        result = self.client._generate_content("Test prompt", "gemini-pro")
        
        assert result == ("Mock string conversion", 75, 150)
        mock_response.__str__.assert_called_once()