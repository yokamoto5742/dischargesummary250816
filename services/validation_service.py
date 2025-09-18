import streamlit as st

from utils.config import (CLAUDE_AVAILABLE, GOOGLE_CREDENTIALS_JSON,
                          MAX_INPUT_TOKENS, MIN_INPUT_TOKENS)
from utils.constants import MESSAGES
from utils.exceptions import APIError


class ValidationService:

    @staticmethod
    def validate_api_credentials() -> None:
        if not any([GOOGLE_CREDENTIALS_JSON, CLAUDE_AVAILABLE]):
            raise APIError(MESSAGES["NO_API_CREDENTIALS"])

    @staticmethod
    def validate_input_text(input_text: str) -> None:
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
        ValidationService.validate_api_credentials()
        ValidationService.validate_input_text(input_text)

    @staticmethod
    def validate_api_credentials_for_provider(provider: str) -> None:
        credentials_check = {
            "claude": CLAUDE_AVAILABLE,
            "gemini": GOOGLE_CREDENTIALS_JSON,
        }

        if not credentials_check.get(provider):
            raise APIError(MESSAGES["NO_API_CREDENTIALS"])
