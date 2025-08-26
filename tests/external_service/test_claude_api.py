import pytest
from unittest.mock import Mock, patch, MagicMock

from external_service.claude_api import ClaudeAPIClient
from utils.exceptions import APIError


class TestClaudeAPIClient:
    
    def setup_method(self):
        with patch('external_service.claude_api.CLAUDE_API_KEY', 'fake_api_key'), \
             patch('external_service.claude_api.CLAUDE_MODEL', 'claude-3-sonnet'):
            self.client = ClaudeAPIClient()

    def test_init(self):
        with patch('external_service.claude_api.CLAUDE_API_KEY', 'test_key'), \
             patch('external_service.claude_api.CLAUDE_MODEL', 'test_model'):
            client = ClaudeAPIClient()
            assert client.api_key == 'test_key'
            assert client.default_model == 'test_model'
            assert client.client is None

    @patch('external_service.claude_api.Anthropic')
    def test_initialize_success(self, mock_anthropic):
        mock_anthropic_instance = Mock()
        mock_anthropic.return_value = mock_anthropic_instance
        
        result = self.client.initialize()
        
        assert result is True
        assert self.client.client is mock_anthropic_instance
        mock_anthropic.assert_called_once_with(api_key='fake_api_key')

    def test_initialize_no_api_key(self):
        client = ClaudeAPIClient()
        client.api_key = None
        
        with pytest.raises(APIError) as exc_info:
            client.initialize()
        assert "Gemini APIの認証情報が設定されていません" in str(exc_info.value)

    @patch('external_service.claude_api.Anthropic')
    def test_initialize_anthropic_exception(self, mock_anthropic):
        mock_anthropic.side_effect = Exception("Connection error")
        
        with pytest.raises(APIError) as exc_info:
            self.client.initialize()
        assert "Claude API初期化エラー" in str(exc_info.value)

    def test_generate_content_success(self):
        # Mock the Anthropic client response
        mock_response = Mock()
        mock_content = Mock()
        mock_content.text = "Generated summary text"
        mock_response.content = [mock_content]
        mock_usage = Mock()
        mock_usage.input_tokens = 150
        mock_usage.output_tokens = 300
        mock_response.usage = mock_usage
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        self.client.client = mock_client
        
        result = self.client._generate_content("Test prompt", "claude-3-sonnet")
        
        assert result == ("Generated summary text", 150, 300)
        mock_client.messages.create.assert_called_once_with(
            model="claude-3-sonnet",
            max_tokens=6000,
            messages=[{"role": "user", "content": "Test prompt"}]
        )

    def test_generate_content_empty_response(self):
        # Mock empty response
        mock_response = Mock()
        mock_response.content = None
        mock_usage = Mock()
        mock_usage.input_tokens = 150
        mock_usage.output_tokens = 0
        mock_response.usage = mock_usage
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        self.client.client = mock_client
        
        result = self.client._generate_content("Test prompt", "claude-3-sonnet")
        
        assert result == ("レスポンスが空です", 150, 0)

    def test_generate_content_empty_content_array(self):
        # Mock response with empty content array
        mock_response = Mock()
        mock_response.content = []
        mock_usage = Mock()
        mock_usage.input_tokens = 150
        mock_usage.output_tokens = 0
        mock_response.usage = mock_usage
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        self.client.client = mock_client
        
        result = self.client._generate_content("Test prompt", "claude-3-sonnet")
        assert result[0] == "レスポンスが空です"
        assert result[1] == 150
        assert result[2] == 0

    def test_generate_content_with_usage_metadata(self):
        # Test with different usage structure
        mock_response = Mock()
        mock_content = Mock()
        mock_content.text = "Generated text"
        mock_response.content = [mock_content]
        mock_usage = Mock()
        mock_usage.input_tokens = 100
        mock_usage.output_tokens = 200
        mock_response.usage = mock_usage
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        self.client.client = mock_client
        
        result = self.client._generate_content("Test prompt", "claude-3-sonnet")
        
        assert result == ("Generated text", 100, 200)

    def test_generate_content_api_exception(self):
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("API call failed")
        self.client.client = mock_client
        
        with pytest.raises(Exception) as exc_info:
            self.client._generate_content("Test prompt", "claude-3-sonnet")
        assert "API call failed" in str(exc_info.value)

    def test_generate_content_with_max_tokens(self):
        mock_response = Mock()
        mock_content = Mock()
        mock_content.text = "Generated text"
        mock_response.content = [mock_content]
        mock_usage = Mock()
        mock_usage.input_tokens = 100
        mock_usage.output_tokens = 200
        mock_response.usage = mock_usage
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        self.client.client = mock_client
        
        self.client._generate_content("Test prompt", "claude-3-sonnet")
        
        # Verify max_tokens is set to 6000
        call_args = mock_client.messages.create.call_args[1]
        assert call_args['max_tokens'] == 6000

    def test_generate_content_message_format(self):
        mock_response = Mock()
        mock_content = Mock()
        mock_content.text = "Generated text"
        mock_response.content = [mock_content]
        mock_usage = Mock()
        mock_usage.input_tokens = 100
        mock_usage.output_tokens = 200
        mock_response.usage = mock_usage
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        self.client.client = mock_client
        
        prompt = "Test prompt with special characters: 日本語"
        self.client._generate_content(prompt, "claude-3-sonnet")
        
        # Verify message format
        call_args = mock_client.messages.create.call_args[1]
        assert call_args['messages'] == [{"role": "user", "content": prompt}]

    @patch('external_service.claude_api.Anthropic')
    def test_integration_initialize_and_generate(self, mock_anthropic):
        # Integration test for initialize and generate_content
        mock_response = Mock()
        mock_content = Mock()
        mock_content.text = "Integration test response"
        mock_response.content = [mock_content]
        mock_usage = Mock()
        mock_usage.input_tokens = 50
        mock_usage.output_tokens = 100
        mock_response.usage = mock_usage
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        # Initialize the client
        result_init = self.client.initialize()
        assert result_init is True
        
        # Generate content
        result_generate = self.client._generate_content("Test prompt", "claude-3-sonnet")
        assert result_generate == ("Integration test response", 50, 100)

    def test_multiple_content_blocks(self):
        # Test response with multiple content blocks (should use first one)
        mock_response = Mock()
        mock_content1 = Mock()
        mock_content1.text = "First content block"
        mock_content2 = Mock()
        mock_content2.text = "Second content block"
        mock_response.content = [mock_content1, mock_content2]
        mock_usage = Mock()
        mock_usage.input_tokens = 100
        mock_usage.output_tokens = 200
        mock_response.usage = mock_usage
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        self.client.client = mock_client
        
        result = self.client._generate_content("Test prompt", "claude-3-sonnet")
        
        # Should return first content block
        assert result == ("First content block", 100, 200)