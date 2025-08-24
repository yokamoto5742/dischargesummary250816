"""
実際のサマリー生成処理を行うサービス
"""
import queue
import threading
import time
from typing import Dict, Any

import streamlit as st

from external_service.api_factory import generate_summary
from services.model_service import ModelService
from services.validation_service import ValidationService
from utils.constants import DEFAULT_DOCUMENT_TYPE
from utils.text_processor import format_output_summary, parse_output_summary


class GenerationService:
    """サマリー生成処理を担当するサービスクラス"""
    
    @staticmethod
    def generate_summary_task(input_text: str, selected_department: str,
                             selected_model: str, result_queue: queue.Queue,
                             additional_info: str = "", current_prescription: str = "",
                             selected_document_type: str = DEFAULT_DOCUMENT_TYPE,
                             selected_doctor: str = "default",
                             model_explicitly_selected: bool = False) -> None:
        """バックグラウンドでのサマリー生成タスク"""
        try:
            generation_params = GenerationService.prepare_generation_parameters(
                selected_department, selected_document_type, selected_doctor,
                selected_model, model_explicitly_selected, input_text, additional_info
            )

            api_result = GenerationService.execute_api_generation(
                generation_params['provider'], generation_params['model_name'],
                input_text, additional_info, current_prescription,
                generation_params['normalized_dept'], generation_params['normalized_doc_type'],
                selected_doctor
            )

            result = GenerationService.format_generation_result(
                api_result['output_summary'], api_result['input_tokens'], api_result['output_tokens'],
                generation_params['model_detail'], generation_params['model_switched'],
                generation_params['original_model']
            )

            result_queue.put(result)

        except Exception as e:
            result_queue.put({
                "success": False,
                "error": str(e)
            })

    @staticmethod
    def prepare_generation_parameters(selected_department: str, selected_document_type: str,
                                    selected_doctor: str, selected_model: str,
                                    model_explicitly_selected: bool, input_text: str,
                                    additional_info: str) -> Dict[str, Any]:
        """生成パラメーターの準備"""
        normalized_dept, normalized_doc_type = ModelService.normalize_selection_params(
            selected_department, selected_document_type
        )

        final_model, model_switched, original_model = ModelService.determine_final_model(
            normalized_dept, normalized_doc_type, selected_doctor,
            selected_model, model_explicitly_selected, input_text, additional_info
        )

        provider, model_name = ModelService.get_provider_and_model(final_model)
        ValidationService.validate_api_credentials_for_provider(provider)

        model_detail = model_name if provider == "gemini" else final_model

        return {
            'normalized_dept': normalized_dept,
            'normalized_doc_type': normalized_doc_type,
            'provider': provider,
            'model_name': model_name,
            'model_detail': model_detail,
            'model_switched': model_switched,
            'original_model': original_model
        }

    @staticmethod
    def execute_api_generation(provider: str, model_name: str, input_text: str,
                             additional_info: str, current_prescription: str,
                             normalized_dept: str, normalized_doc_type: str,
                             selected_doctor: str) -> Dict[str, Any]:
        """API呼び出しの実行"""
        output_summary, input_tokens, output_tokens = generate_summary(
            provider=provider,
            medical_text=input_text,
            additional_info=additional_info,
            current_prescription=current_prescription,
            department=normalized_dept,
            document_type=normalized_doc_type,
            doctor=selected_doctor,
            model_name=model_name
        )

        return {
            'output_summary': output_summary,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens
        }

    @staticmethod
    def format_generation_result(output_summary: str, input_tokens: int, output_tokens: int,
                               model_detail: str, model_switched: bool,
                               original_model: str) -> Dict[str, Any]:
        """生成結果のフォーマット"""
        formatted_summary = format_output_summary(output_summary)
        parsed_summary = parse_output_summary(formatted_summary)

        return {
            "success": True,
            "output_summary": formatted_summary,
            "parsed_summary": parsed_summary,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "model_detail": model_detail,
            "model_switched": model_switched,
            "original_model": original_model if model_switched else None
        }

    @staticmethod
    def display_progress_with_timer(thread: threading.Thread,
                                  placeholder: st.empty,
                                  start_time) -> None:
        """進捗表示とタイマー"""
        import datetime
        
        elapsed_time = 0
        with st.spinner("作成中..."):
            placeholder.text(f"⏱️ 経過時間: {elapsed_time}秒")
            while thread.is_alive():
                time.sleep(1)
                elapsed_time = int((datetime.datetime.now() - start_time).total_seconds())
                placeholder.text(f"⏱️ 経過時間: {elapsed_time}秒")
