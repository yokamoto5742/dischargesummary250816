import pytest
from unittest.mock import Mock, patch
from enum import Enum

from external_service.api_factory import APIFactory, APIProvider, generate_summary
from external_service.base_api import BaseAPIClient
from external_service.claude_api import ClaudeAPIClient
from external_service.gemini_api import GeminiAPIClient
from utils.exceptions import APIError


class TestAPIProvider:
    
    def test_api_provider_enum_values(self):
        assert APIProvider.CLAUDE.value == "claude"
        assert APIProvider.GEMINI.value == "gemini"

    def test_api_provider_enum_count(self):
        # Ensure we have exactly the expected number of providers
        assert len(APIProvider) == 2


class TestAPIFactory:
    
    def test_create_client_with_enum_claude(self):
        client = APIFactory.create_client(APIProvider.CLAUDE)
        assert isinstance(client, ClaudeAPIClient)

    def test_create_client_with_enum_gemini(self):
        client = APIFactory.create_client(APIProvider.GEMINI)
        assert isinstance(client, GeminiAPIClient)

    def test_create_client_with_string_claude(self):
        client = APIFactory.create_client("claude")
        assert isinstance(client, ClaudeAPIClient)

    def test_create_client_with_string_gemini(self):
        client = APIFactory.create_client("gemini")
        assert isinstance(client, GeminiAPIClient)

    def test_create_client_with_string_uppercase(self):
        client = APIFactory.create_client("CLAUDE")
        assert isinstance(client, ClaudeAPIClient)

    def test_create_client_with_string_mixed_case(self):
        client = APIFactory.create_client("Gemini")
        assert isinstance(client, GeminiAPIClient)

    def test_create_client_with_invalid_string(self):
        with pytest.raises(APIError) as exc_info:
            APIFactory.create_client("invalid_provider")
        assert "未対応のAPIプロバイダー" in str(exc_info.value)

    def test_create_client_with_invalid_enum_value(self):
        # This would be a programming error, but let's test it
        class FakeProvider(Enum):
            FAKE = "fake"
        
        with pytest.raises(APIError) as exc_info:
            APIFactory.create_client(FakeProvider.FAKE)
        assert "未対応のAPIプロバイダー" in str(exc_info.value)

    def test_generate_summary_with_provider_enum(self):
        with patch.object(APIFactory, 'create_client') as mock_create_client:
            mock_client = Mock(spec=BaseAPIClient)
            mock_client.generate_summary.return_value = ("summary", 100, 200)
            mock_create_client.return_value = mock_client
            
            result = APIFactory.generate_summary_with_provider(
                APIProvider.CLAUDE,
                "medical_text",
                additional_info="info",
                current_prescription="prescription",
                department="dept",
                document_type="doc_type",
                doctor="doctor",
                model_name="model"
            )
            
            assert result == ("summary", 100, 200)
            mock_create_client.assert_called_once_with(APIProvider.CLAUDE)
            mock_client.generate_summary.assert_called_once_with(
                "medical_text", "info", "prescription", "dept", "doc_type", "doctor", "model"
            )

    def test_generate_summary_with_provider_string(self):
        with patch.object(APIFactory, 'create_client') as mock_create_client:
            mock_client = Mock(spec=BaseAPIClient)
            mock_client.generate_summary.return_value = ("summary", 100, 200)
            mock_create_client.return_value = mock_client
            
            result = APIFactory.generate_summary_with_provider(
                "gemini",
                "medical_text"
            )
            
            mock_create_client.assert_called_once_with("gemini")
            mock_client.generate_summary.assert_called_once()

    def test_generate_summary_with_provider_default_parameters(self):
        with patch.object(APIFactory, 'create_client') as mock_create_client:
            mock_client = Mock(spec=BaseAPIClient)
            mock_client.generate_summary.return_value = ("summary", 100, 200)
            mock_create_client.return_value = mock_client
            
            result = APIFactory.generate_summary_with_provider(
                APIProvider.CLAUDE,
                "medical_text"
            )
            
            mock_client.generate_summary.assert_called_once_with(
                "medical_text", "", "", "default", "退院時サマリ", "default", None
            )

    def test_generate_summary_with_provider_all_parameters(self):
        with patch.object(APIFactory, 'create_client') as mock_create_client:
            mock_client = Mock(spec=BaseAPIClient)
            mock_client.generate_summary.return_value = ("summary", 100, 200)
            mock_create_client.return_value = mock_client
            
            result = APIFactory.generate_summary_with_provider(
                APIProvider.GEMINI,
                "medical_text",
                additional_info="additional",
                current_prescription="prescription",
                department="department",
                document_type="document_type",
                doctor="doctor",
                model_name="model_name"
            )
            
            mock_client.generate_summary.assert_called_once_with(
                "medical_text", "additional", "prescription", 
                "department", "document_type", "doctor", "model_name"
            )

    def test_generate_summary_with_provider_client_exception(self):
        with patch.object(APIFactory, 'create_client') as mock_create_client:
            mock_client = Mock(spec=BaseAPIClient)
            mock_client.generate_summary.side_effect = Exception("API Error")
            mock_create_client.return_value = mock_client
            
            with pytest.raises(Exception) as exc_info:
                APIFactory.generate_summary_with_provider(
                    APIProvider.CLAUDE,
                    "medical_text"
                )
            assert "API Error" in str(exc_info.value)

    def test_generate_summary_with_provider_creation_exception(self):
        with patch.object(APIFactory, 'create_client') as mock_create_client:
            mock_create_client.side_effect = APIError("Provider not supported")
            
            with pytest.raises(APIError) as exc_info:
                APIFactory.generate_summary_with_provider(
                    "invalid_provider",
                    "medical_text"
                )
            assert "Provider not supported" in str(exc_info.value)


class TestGenerateSummaryFunction:
    
    def test_generate_summary_function(self):
        with patch.object(APIFactory, 'generate_summary_with_provider') as mock_generate:
            mock_generate.return_value = ("summary", 100, 200)
            
            result = generate_summary(
                "claude", 
                "medical_text",
                additional_info="info",
                department="dept"
            )
            
            assert result == ("summary", 100, 200)
            mock_generate.assert_called_once_with(
                "claude", 
                "medical_text",
                additional_info="info",
                department="dept"
            )

    def test_generate_summary_function_minimal_params(self):
        with patch.object(APIFactory, 'generate_summary_with_provider') as mock_generate:
            mock_generate.return_value = ("summary", 100, 200)
            
            result = generate_summary("gemini", "medical_text")
            
            assert result == ("summary", 100, 200)
            mock_generate.assert_called_once_with("gemini", "medical_text")

    def test_generate_summary_function_with_kwargs(self):
        with patch.object(APIFactory, 'generate_summary_with_provider') as mock_generate:
            mock_generate.return_value = ("summary", 100, 200)
            
            kwargs = {
                "additional_info": "info",
                "current_prescription": "prescription",
                "department": "dept",
                "document_type": "doc_type",
                "doctor": "doctor",
                "model_name": "model"
            }
            
            result = generate_summary("claude", "medical_text", **kwargs)
            
            assert result == ("summary", 100, 200)
            mock_generate.assert_called_once_with("claude", "medical_text", **kwargs)

    def test_generate_summary_function_exception_propagation(self):
        with patch.object(APIFactory, 'generate_summary_with_provider') as mock_generate:
            mock_generate.side_effect = APIError("Test error")
            
            with pytest.raises(APIError) as exc_info:
                generate_summary("claude", "medical_text")
            assert "Test error" in str(exc_info.value)