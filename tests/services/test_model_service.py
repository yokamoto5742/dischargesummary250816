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
    @patch('services.model_service.GOOGLE_CREDENTIALS_JSON', "fake_credentials")
    @patch('services.model_service.GEMINI_MODEL', "gemini-pro")
    def test_check_model_switching_for_token_limit_switch_to_gemini(self):
        input_text = "very long text that exceeds the token limit"
        additional_info = "additional information that makes it even longer"
        
        result = ModelService.check_model_switching_for_token_limit(
            "Claude", input_text, additional_info
        )
        
        assert result == ("Gemini_Pro", True, "Claude")

    @patch('services.model_service.MAX_TOKEN_THRESHOLD', 10)
    @patch('services.model_service.GOOGLE_CREDENTIALS_JSON', None)
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

    @patch('services.model_service.ANTHROPIC_MODEL', "apac.anthropic.claude-sonnet-4-20250514-v1:0")
    @patch('services.model_service.GEMINI_MODEL', "gemini-pro")
    def test_get_provider_and_model_all_options(self):
        test_cases = [
            ("Claude", ("claude", "apac.anthropic.claude-sonnet-4-20250514-v1:0")),
            ("Gemini_Pro", ("gemini", "gemini-pro"))
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

    # === 詳細なcheck_model_switching_for_token_limit()テスト ===
    
    @patch('services.model_service.MAX_TOKEN_THRESHOLD', 5000)
    @patch('services.model_service.GOOGLE_CREDENTIALS_JSON', "test_credentials")
    @patch('services.model_service.GEMINI_MODEL', "gemini-1.5-pro")
    def test_check_model_switching_claude_exceeds_threshold_with_gemini(self):
        """Claudeがトークン制限を超過し、Geminiが利用可能な場合のテスト"""
        # 5000文字を超える文字列を作成
        long_input_text = "あ" * 3000
        long_additional_info = "い" * 2500  # 合計5500文字
        
        result = ModelService.check_model_switching_for_token_limit(
            "Claude", long_input_text, long_additional_info
        )
        
        assert result[0] == "Gemini_Pro"  # 切り替え先のモデル
        assert result[1] is True  # モデルが切り替えられた
        assert result[2] == "Claude"  # 元のモデル

    @patch('services.model_service.MAX_TOKEN_THRESHOLD', 5000)
    @patch('services.model_service.GOOGLE_CREDENTIALS_JSON', None)
    @patch('services.model_service.GEMINI_MODEL', None)
    def test_check_model_switching_claude_exceeds_threshold_no_gemini(self):
        """Claudeがトークン制限を超過し、Geminiが利用不可な場合のエラーテスト"""
        long_input_text = "あ" * 3000
        long_additional_info = "い" * 2500
        
        with pytest.raises(APIError) as exc_info:
            ModelService.check_model_switching_for_token_limit(
                "Claude", long_input_text, long_additional_info
            )
        
        # エラーメッセージの確認
        assert "Gemini APIの認証情報が設定されていないため処理できません" in str(exc_info.value)

    @patch('services.model_service.MAX_TOKEN_THRESHOLD', 1000)
    def test_check_model_switching_claude_under_threshold(self):
        """Claudeがトークン制限内の場合のテスト"""
        input_text = "短いテキスト"
        additional_info = "追加情報"
        
        result = ModelService.check_model_switching_for_token_limit(
            "Claude", input_text, additional_info
        )
        
        assert result[0] == "Claude"  # モデル変更なし
        assert result[1] is False  # 切り替えなし
        assert result[2] == "Claude"  # 元のモデル

    @patch('services.model_service.MAX_TOKEN_THRESHOLD', 100)
    def test_check_model_switching_gemini_exceeds_threshold(self):
        """Geminiがトークン制限を超過してもそのまま使用されることのテスト"""
        long_input_text = "あ" * 150  # 制限を超える文字数
        additional_info = ""
        
        result = ModelService.check_model_switching_for_token_limit(
            "Gemini_Pro", long_input_text, additional_info
        )
        
        assert result[0] == "Gemini_Pro"  # そのまま
        assert result[1] is False  # 切り替えなし
        assert result[2] == "Gemini_Pro"  # 元のモデル

    def test_check_model_switching_empty_strings(self):
        """空文字列の入力テスト"""
        result = ModelService.check_model_switching_for_token_limit(
            "Claude", "", ""
        )
        
        assert result[0] == "Claude"
        assert result[1] is False
        assert result[2] == "Claude"

    @patch('services.model_service.MAX_TOKEN_THRESHOLD', 50)
    def test_check_model_switching_exactly_threshold(self):
        """ちょうどしきい値の文字数の場合のテスト"""
        input_text = "あ" * 50  # ちょうど50文字
        additional_info = ""
        
        result = ModelService.check_model_switching_for_token_limit(
            "Claude", input_text, additional_info
        )
        
        # しきい値以下なので切り替えなし
        assert result[0] == "Claude"
        assert result[1] is False
        assert result[2] == "Claude"

    @patch('services.model_service.MAX_TOKEN_THRESHOLD', 50)
    @patch('services.model_service.GOOGLE_CREDENTIALS_JSON', "test_creds")
    @patch('services.model_service.GEMINI_MODEL', "gemini-model")
    def test_check_model_switching_one_over_threshold(self):
        """しきい値を1文字超える場合のテスト"""
        input_text = "あ" * 51  # 51文字（しきい値+1）
        additional_info = ""
        
        result = ModelService.check_model_switching_for_token_limit(
            "Claude", input_text, additional_info
        )
        
        # しきい値を超えたので切り替え
        assert result[0] == "Gemini_Pro"
        assert result[1] is True
        assert result[2] == "Claude"

    @patch('services.model_service.MAX_TOKEN_THRESHOLD', 100)
    @patch('services.model_service.GOOGLE_CREDENTIALS_JSON', "test_creds")
    @patch('services.model_service.GEMINI_MODEL', "gemini-model")
    def test_check_model_switching_additional_info_none(self):
        """additional_infoがNoneの場合のテスト"""
        input_text = "あ" * 150  # しきい値超え
        additional_info = None
        
        result = ModelService.check_model_switching_for_token_limit(
            "Claude", input_text, additional_info
        )
        
        assert result[0] == "Gemini_Pro"
        assert result[1] is True
        assert result[2] == "Claude"

    @patch('services.model_service.MAX_TOKEN_THRESHOLD', 100)
    @patch('services.model_service.GOOGLE_CREDENTIALS_JSON', "test_creds")  
    @patch('services.model_service.GEMINI_MODEL', "gemini-model")
    def test_check_model_switching_combined_text_exceeds(self):
        """入力テキストと追加情報の合計でしきい値を超える場合のテスト"""
        input_text = "あ" * 60  # 60文字
        additional_info = "い" * 50  # 50文字、合計110文字
        
        result = ModelService.check_model_switching_for_token_limit(
            "Claude", input_text, additional_info
        )
        
        assert result[0] == "Gemini_Pro"
        assert result[1] is True
        assert result[2] == "Claude"

    @patch('services.model_service.MAX_TOKEN_THRESHOLD', 200)
    @patch('services.model_service.GOOGLE_CREDENTIALS_JSON', "")  # 空文字列
    @patch('services.model_service.GEMINI_MODEL', "gemini-model")
    def test_check_model_switching_empty_gemini_credentials(self):
        """Gemini認証情報が空文字列の場合のテスト"""
        long_input_text = "あ" * 250
        
        with pytest.raises(APIError):
            ModelService.check_model_switching_for_token_limit(
                "Claude", long_input_text, ""
            )

    @patch('services.model_service.MAX_TOKEN_THRESHOLD', 200)
    @patch('services.model_service.GOOGLE_CREDENTIALS_JSON', "test_creds")
    @patch('services.model_service.GEMINI_MODEL', "")  # 空文字列
    def test_check_model_switching_empty_gemini_model(self):
        """Geminiモデル名が空文字列の場合のテスト"""
        long_input_text = "あ" * 250
        
        with pytest.raises(APIError):
            ModelService.check_model_switching_for_token_limit(
                "Claude", long_input_text, ""
            )