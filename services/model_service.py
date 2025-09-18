from typing import Tuple

from utils.config import (ANTHROPIC_MODEL, GOOGLE_CREDENTIALS_JSON,
                          GEMINI_FLASH_MODEL, GEMINI_MODEL, MAX_TOKEN_THRESHOLD)
from utils.constants import DEFAULT_DEPARTMENT, DOCUMENT_TYPES, MESSAGES
from utils.exceptions import APIError
from utils.prompt_manager import get_prompt_manager


class ModelService:
    
    @staticmethod
    def determine_final_model(department: str, document_type: str,
                             doctor: str, selected_model: str,
                             model_explicitly_selected: bool, input_text: str,
                             additional_info: str) -> Tuple[str, bool, str]:
        final_model = ModelService.get_model_from_prompt_if_needed(
            department, document_type, doctor, selected_model, model_explicitly_selected
        )

        return ModelService.check_model_switching_for_token_limit(
            final_model, input_text, additional_info
        )

    @staticmethod
    def get_model_from_prompt_if_needed(department: str, document_type: str, doctor: str,
                                       selected_model: str, model_explicitly_selected: bool) -> str:
        if model_explicitly_selected:
            return selected_model

        prompt_data = get_prompt_manager().get_prompt(department, document_type, doctor)
        prompt_selected_model = prompt_data.get("selected_model") if prompt_data else None

        return prompt_selected_model or selected_model

    @staticmethod
    def check_model_switching_for_token_limit(selected_model: str, input_text: str,
                                            additional_info: str) -> Tuple[str, bool, str]:
        total_characters = len(input_text) + len(additional_info or "")
        original_model = selected_model
        model_switched = False

        if selected_model == "Claude" and total_characters > MAX_TOKEN_THRESHOLD:
            if GOOGLE_CREDENTIALS_JSON and GEMINI_MODEL:
                selected_model = "Gemini_Pro"
                model_switched = True
            else:
                raise APIError(MESSAGES["TOKEN_THRESHOLD_EXCEEDED_NO_GEMINI"])

        return selected_model, model_switched, original_model

    @staticmethod
    def get_provider_and_model(selected_model: str) -> Tuple[str, str]:
        provider_mapping = {
            "Claude": ("claude", ANTHROPIC_MODEL),
            "Gemini_Pro": ("gemini", GEMINI_MODEL),
            "Gemini_Flash": ("gemini", GEMINI_FLASH_MODEL),
        }

        if selected_model not in provider_mapping:
            raise APIError(MESSAGES["NO_API_CREDENTIALS"])

        return provider_mapping[selected_model]

    @staticmethod
    def normalize_selection_params(department: str, document_type: str) -> Tuple[str, str]:
        normalized_dept = department if department in DEFAULT_DEPARTMENT else "default"
        normalized_doc_type = document_type if document_type in DOCUMENT_TYPES else DOCUMENT_TYPES[0]
        return normalized_dept, normalized_doc_type
