import os
import pytest
from unittest.mock import Mock, patch

from external_service.gemini_api import GeminiAPIClient
from utils.exceptions import APIError


class TestGeminiAPIClient:
    
    def setup_method(self):
        # Using valid JSON for GOOGLE_CREDENTIALS_JSON
        fake_credentials_json = '{"type": "service_account", "project_id": "test-project", "private_key_id": "test-key-id", "private_key": "-----BEGIN PRIVATE KEY-----\\ntest-private-key\\n-----END PRIVATE KEY-----\\n", "client_email": "test@test-project.iam.gserviceaccount.com", "client_id": "test-client-id", "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token"}'
        with patch.dict(os.environ, {'GOOGLE_CREDENTIALS_JSON': fake_credentials_json}), \
             patch('external_service.gemini_api.GEMINI_MODEL', 'gemini-pro'), \
             patch('external_service.gemini_api.GOOGLE_PROJECT_ID', 'gen-lang-client-0605794434'), \
             patch('external_service.gemini_api.GOOGLE_LOCATION', 'us-west1'):
            self.client = GeminiAPIClient()

    def test_init(self):
        test_credentials_json = '{"type": "service_account", "project_id": "test-project"}'
        with patch.dict(os.environ, {'GOOGLE_CREDENTIALS_JSON': test_credentials_json}), \
             patch('external_service.gemini_api.GEMINI_MODEL', 'test_model'):
            client = GeminiAPIClient()
            # GeminiAPIClient no longer has api_key attribute
            assert client.default_model == 'test_model'
            assert client.client is None

    @patch('external_service.gemini_api.service_account')
    @patch('external_service.gemini_api.genai')
    def test_initialize_success(self, mock_genai, mock_service_account):
        mock_client_instance = Mock()
        mock_genai.Client.return_value = mock_client_instance
        mock_credentials = Mock()
        mock_service_account.Credentials.from_service_account_info.return_value = mock_credentials

        result = self.client.initialize()

        assert result is True
        assert self.client.client is mock_client_instance
        mock_genai.Client.assert_called_once_with(
            vertexai=True,
            project='gen-lang-client-0605794434',
            location='us-west1',
            credentials=mock_credentials
        )

    @patch('external_service.gemini_api.GOOGLE_PROJECT_ID', None)
    def test_initialize_no_google_credentials(self):
        client = GeminiAPIClient()

        with pytest.raises(APIError) as exc_info:
            client.initialize()
        assert "GOOGLE_PROJECT_ID環境変数が設定されていません" in str(exc_info.value)

    @patch('external_service.gemini_api.service_account')
    @patch('external_service.gemini_api.genai')
    def test_initialize_genai_exception(self, mock_genai, mock_service_account):
        mock_service_account.Credentials.from_service_account_info.side_effect = Exception("Connection error")

        with pytest.raises(APIError) as exc_info:
            self.client.initialize()
        assert "認証情報の作成エラー" in str(exc_info.value)

    @patch('external_service.gemini_api.GOOGLE_PROJECT_ID', None)
    def test_initialize_no_project_id(self):
        with pytest.raises(APIError) as exc_info:
            self.client.initialize()
        assert "GOOGLE_PROJECT_ID環境変数が設定されていません" in str(exc_info.value)

    @patch('external_service.gemini_api.GOOGLE_LOCATION', None)
    def test_initialize_no_location(self):
        with pytest.raises(APIError) as exc_info:
            self.client.initialize()
        assert "認証情報の作成エラー" in str(exc_info.value)

    @patch.dict(os.environ, {}, clear=True)
    @patch('external_service.gemini_api.GOOGLE_PROJECT_ID', 'test-project')
    @patch('external_service.gemini_api.GOOGLE_LOCATION', 'us-west1')
    @patch('external_service.gemini_api.genai')
    def test_initialize_without_credentials_json(self, mock_genai):
        mock_client_instance = Mock()
        mock_genai.Client.return_value = mock_client_instance
        client = GeminiAPIClient()

        result = client.initialize()

        assert result is True
        assert client.client is mock_client_instance
        mock_genai.Client.assert_called_once_with(
            vertexai=True,
            project='test-project',
            location='us-west1'
        )

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

        with pytest.raises(APIError) as exc_info:
            self.client._generate_content("Test prompt", "gemini-pro")
        assert "Vertex AI Gemini APIエラー" in str(exc_info.value)

    def test_generate_content_api_exception(self):
        mock_client = Mock()
        mock_client.models.generate_content.side_effect = Exception("API call failed")
        self.client.client = mock_client

        with pytest.raises(APIError) as exc_info:
            self.client._generate_content("Test prompt", "gemini-pro")
        assert "Vertex AI Gemini APIエラー" in str(exc_info.value)
        assert "API call failed" in str(exc_info.value)

    @patch('external_service.gemini_api.service_account')
    @patch('external_service.gemini_api.genai')
    def test_integration_initialize_and_generate(self, mock_genai, mock_service_account):
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
        mock_credentials = Mock()
        mock_service_account.Credentials.from_service_account_info.return_value = mock_credentials

        # Initialize the client
        result_init = self.client.initialize()
        assert result_init is True

        # Verify Vertex AI client was created correctly
        mock_genai.Client.assert_called_once_with(
            vertexai=True,
            project='gen-lang-client-0605794434',
            location='us-west1',
            credentials=mock_credentials
        )
        
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
        mock_client.models.generate_content.assert_called_once()
        call_args = mock_client.models.generate_content.call_args
        assert call_args[1]['model'] == "gemini-pro"
        assert call_args[1]['contents'] == complex_prompt

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