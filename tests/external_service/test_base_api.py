import pytest
from unittest.mock import Mock, patch
from abc import ABC

from external_service.base_api import BaseAPIClient
from utils.exceptions import APIError


class ConcreteAPIClient(BaseAPIClient):
    """Concrete implementation of BaseAPIClient for testing"""
    
    def initialize(self) -> bool:
        return True if self.api_key else False
    
    def _generate_content(self, prompt: str, model_name: str):
        return ("Generated content", 100, 200)


class TestBaseAPIClient:
    
    def setup_method(self):
        self.client = ConcreteAPIClient("fake_api_key", "fake_model")

    def test_init(self):
        api_key = "test_api_key"
        default_model = "test_model"
        client = ConcreteAPIClient(api_key, default_model)
        
        assert client.api_key == api_key
        assert client.default_model == default_model

    def test_abstract_class_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            BaseAPIClient("api_key", "model")

    def test_create_summary_prompt_basic(self):
        with patch('external_service.base_api.get_prompt_manager') as mock_get_manager, \
             patch('external_service.base_api.get_config') as mock_get_config:
            
            mock_manager = Mock()
            mock_manager.get_prompt.return_value = {"content": "Custom prompt template"}
            mock_get_manager.return_value = mock_manager
            
            result = self.client.create_summary_prompt(
                "Medical text",
                additional_info="Additional info",
                current_prescription="Prescription info",
                department="dept",
                document_type="doc_type",
                doctor="doctor"
            )
            
            expected = ("Custom prompt template\n【カルテ情報】\nMedical text"
                       "\n【現在の処方】\nPrescription info"
                       "\n【追加情報】Additional info")
            
            assert result == expected
            mock_manager.get_prompt.assert_called_once_with("dept", "doc_type", "doctor")

    def test_create_summary_prompt_no_prompt_data(self):
        with patch('external_service.base_api.get_prompt_manager') as mock_get_manager, \
             patch('external_service.base_api.get_config') as mock_get_config:
            
            mock_manager = Mock()
            mock_manager.get_prompt.return_value = None
            mock_get_manager.return_value = mock_manager
            
            mock_config = {"PROMPTS": {"summary": "Default prompt template"}}
            mock_get_config.return_value = mock_config
            
            result = self.client.create_summary_prompt(
                "Medical text",
                additional_info="Additional info"
            )
            
            expected = ("Default prompt template\n【カルテ情報】\nMedical text"
                       "\n【追加情報】Additional info")
            
            assert result == expected

    def test_create_summary_prompt_empty_prescription(self):
        with patch('external_service.base_api.get_prompt_manager') as mock_get_manager:
            
            mock_manager = Mock()
            mock_manager.get_prompt.return_value = {"content": "Template"}
            mock_get_manager.return_value = mock_manager
            
            result = self.client.create_summary_prompt(
                "Medical text",
                current_prescription="",
                additional_info="Additional info"
            )
            
            # Should not include prescription section when empty
            assert "【現在の処方】" not in result
            assert "【カルテ情報】\nMedical text" in result
            assert "【追加情報】Additional info" in result

    def test_create_summary_prompt_whitespace_prescription(self):
        with patch('external_service.base_api.get_prompt_manager') as mock_get_manager:
            
            mock_manager = Mock()
            mock_manager.get_prompt.return_value = {"content": "Template"}
            mock_get_manager.return_value = mock_manager
            
            result = self.client.create_summary_prompt(
                "Medical text",
                current_prescription="   \n  \t  ",
                additional_info="Additional info"
            )
            
            # Should not include prescription section when only whitespace
            assert "【現在の処方】" not in result

    def test_create_summary_prompt_default_params(self):
        with patch('external_service.base_api.get_prompt_manager') as mock_get_manager, \
             patch('external_service.base_api.DEFAULT_DOCUMENT_TYPE', '退院時サマリ'):
            
            mock_manager = Mock()
            mock_manager.get_prompt.return_value = {"content": "Template"}
            mock_get_manager.return_value = mock_manager
            
            result = self.client.create_summary_prompt("Medical text")
            
            expected = "Template\n【カルテ情報】\nMedical text\n【追加情報】"
            assert result == expected
            mock_manager.get_prompt.assert_called_once_with("default", "退院時サマリ", "default")

    def test_get_model_name_with_prompt_model(self):
        with patch('external_service.base_api.get_prompt_manager') as mock_get_manager:
            
            mock_manager = Mock()
            mock_manager.get_prompt.return_value = {"selected_model": "custom_model"}
            mock_get_manager.return_value = mock_manager
            
            result = self.client.get_model_name("dept", "doc_type", "doctor")
            
            assert result == "custom_model"
            mock_manager.get_prompt.assert_called_once_with("dept", "doc_type", "doctor")

    def test_get_model_name_no_prompt_model(self):
        with patch('external_service.base_api.get_prompt_manager') as mock_get_manager:
            
            mock_manager = Mock()
            mock_manager.get_prompt.return_value = {"selected_model": None}
            mock_get_manager.return_value = mock_manager
            
            result = self.client.get_model_name("dept", "doc_type", "doctor")
            
            assert result == "fake_model"  # Should return default_model

    def test_get_model_name_no_prompt_data(self):
        with patch('external_service.base_api.get_prompt_manager') as mock_get_manager:
            
            mock_manager = Mock()
            mock_manager.get_prompt.return_value = None
            mock_get_manager.return_value = mock_manager
            
            result = self.client.get_model_name("dept", "doc_type", "doctor")
            
            assert result == "fake_model"  # Should return default_model

    def test_get_model_name_empty_selected_model(self):
        with patch('external_service.base_api.get_prompt_manager') as mock_get_manager:
            
            mock_manager = Mock()
            mock_manager.get_prompt.return_value = {"selected_model": ""}
            mock_get_manager.return_value = mock_manager
            
            result = self.client.get_model_name("dept", "doc_type", "doctor")
            
            assert result == "fake_model"  # Should return default_model for empty string

    def test_generate_summary_success(self):
        with patch.object(self.client, 'initialize') as mock_init, \
             patch.object(self.client, 'create_summary_prompt') as mock_create_prompt, \
             patch.object(self.client, '_generate_content') as mock_generate:
            
            mock_init.return_value = True
            mock_create_prompt.return_value = "Generated prompt"
            mock_generate.return_value = ("Summary", 100, 200)
            
            result = self.client.generate_summary(
                "medical_text",
                additional_info="info",
                current_prescription="prescription",
                department="dept",
                document_type="doc_type",
                doctor="doctor",
                model_name="custom_model"
            )
            
            assert result == ("Summary", 100, 200)
            mock_init.assert_called_once()
            mock_create_prompt.assert_called_once_with(
                "medical_text", "info", "prescription", "dept", "doc_type"
            )
            mock_generate.assert_called_once_with("Generated prompt", "custom_model")

    def test_generate_summary_no_model_name(self):
        with patch.object(self.client, 'initialize') as mock_init, \
             patch.object(self.client, 'get_model_name') as mock_get_model_name, \
             patch.object(self.client, 'create_summary_prompt') as mock_create_prompt, \
             patch.object(self.client, '_generate_content') as mock_generate:
            
            mock_init.return_value = True
            mock_get_model_name.return_value = "model_from_prompt"
            mock_create_prompt.return_value = "Generated prompt"
            mock_generate.return_value = ("Summary", 100, 200)
            
            result = self.client.generate_summary("medical_text")
            
            assert result == ("Summary", 100, 200)
            mock_get_model_name.assert_called_once_with("default", "退院時サマリ", "default")
            mock_generate.assert_called_once_with("Generated prompt", "model_from_prompt")

    def test_generate_summary_api_error_propagation(self):
        with patch.object(self.client, 'initialize') as mock_init:
            mock_init.side_effect = APIError("API initialization failed")
            
            with pytest.raises(APIError) as exc_info:
                self.client.generate_summary("medical_text")
            assert "API initialization failed" in str(exc_info.value)

    def test_generate_summary_general_exception_handling(self):
        with patch.object(self.client, 'initialize') as mock_init:
            mock_init.side_effect = Exception("General error")
            
            with pytest.raises(APIError) as exc_info:
                self.client.generate_summary("medical_text")
            assert "ConcreteAPIClient" in str(exc_info.value)
            assert "General error" in str(exc_info.value)

    def test_generate_summary_create_prompt_exception(self):
        with patch.object(self.client, 'initialize') as mock_init, \
             patch('external_service.base_api.get_prompt_manager') as mock_get_manager, \
             patch.object(self.client, 'create_summary_prompt') as mock_create_prompt:
            
            mock_init.return_value = True
            mock_manager = Mock()
            mock_manager.get_prompt.side_effect = Exception("Prompt creation failed")
            mock_get_manager.return_value = mock_manager
            mock_create_prompt.side_effect = Exception("Prompt creation failed")
            
            with pytest.raises(APIError) as exc_info:
                self.client.generate_summary("medical_text")
            assert "ConcreteAPIClient" in str(exc_info.value)
            assert "Prompt creation failed" in str(exc_info.value)

    def test_generate_summary_generate_content_exception(self):
        with patch.object(self.client, 'initialize') as mock_init, \
             patch('external_service.base_api.get_prompt_manager') as mock_get_manager, \
             patch.object(self.client, 'create_summary_prompt') as mock_create_prompt, \
             patch.object(self.client, '_generate_content') as mock_generate:
            
            mock_init.return_value = True
            mock_manager = Mock()
            mock_manager.get_prompt.return_value = {"content": "test prompt"}
            mock_get_manager.return_value = mock_manager
            mock_create_prompt.return_value = "Generated prompt"
            mock_generate.side_effect = Exception("Content generation failed")
            
            with pytest.raises(APIError) as exc_info:
                self.client.generate_summary("medical_text")
            assert "ConcreteAPIClient" in str(exc_info.value)
            assert "Content generation failed" in str(exc_info.value)

    def test_generate_summary_with_default_document_type(self):
        with patch.object(self.client, 'initialize') as mock_init, \
             patch('external_service.base_api.get_prompt_manager') as mock_get_manager, \
             patch.object(self.client, 'create_summary_prompt') as mock_create_prompt, \
             patch.object(self.client, '_generate_content') as mock_generate, \
             patch('external_service.base_api.DEFAULT_DOCUMENT_TYPE', '退院時サマリ'):
            
            mock_init.return_value = True
            mock_manager = Mock()
            mock_manager.get_prompt.return_value = {"content": "test prompt"}
            mock_get_manager.return_value = mock_manager
            mock_create_prompt.return_value = "Generated prompt"
            mock_generate.return_value = ("Summary", 100, 200)
            
            self.client.generate_summary("medical_text")

            mock_create_prompt.assert_called_once_with(
                "medical_text", "", "", "default", "退院時サマリ"
            )