"""
入力検証とAPI認証情報の検証を行うサービス
"""
import streamlit as st

from utils.config import (CLAUDE_API_KEY, GEMINI_CREDENTIALS, 
                         MAX_INPUT_TOKENS, MIN_INPUT_TOKENS)
from utils.constants import MESSAGES
from utils.exceptions import APIError


class ValidationService:
    """入力検証とAPI認証情報の検証を担当するサービスクラス"""
    
    @staticmethod
    def validate_api_credentials() -> None:
        """APIクレデンシャルの存在確認"""
        if not any([GEMINI_CREDENTIALS, CLAUDE_API_KEY]):
            raise APIError(MESSAGES["NO_API_CREDENTIALS"])

    @staticmethod
    def validate_input_text(input_text: str) -> None:
        """入力テキストの妥当性を検証"""
        if not input_text:
            st.warning(MESSAGES["NO_INPUT"])
            return

        input_length = len(input_text.strip())
        if input_length < MIN_INPUT_TOKENS:
            st.warning(f"{MESSAGES['INPUT_TOO_SHORT']}")
            return

        if input_length > MAX_INPUT_TOKENS:
            st.warning(f"{MESSAGES['INPUT_TOO_LONG']}")
            return

    @staticmethod
    def validate_inputs(input_text: str) -> None:
        """全体的な入力検証"""
        ValidationService.validate_api_credentials()
        ValidationService.validate_input_text(input_text)

    @staticmethod
    def validate_api_credentials_for_provider(provider: str) -> None:
        """特定のプロバイダーのAPIクレデンシャルを検証"""
        credentials_check = {
            "claude": CLAUDE_API_KEY,
            "gemini": GEMINI_CREDENTIALS,
        }

        if not credentials_check.get(provider):
            raise APIError(MESSAGES["NO_API_CREDENTIALS"])
