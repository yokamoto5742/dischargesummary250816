"""
サマリー生成のメイン処理とオーケストレーションを行うサービス
"""
import datetime
import queue
import threading
from typing import Dict, Any

import streamlit as st

from services.generation_service import GenerationService
from services.statistics_service import StatisticsService
from services.validation_service import ValidationService
from utils.error_handlers import handle_error
from utils.exceptions import APIError


class SummaryService:
    """サマリー生成のメインオーケストレーションを担当するサービスクラス"""
    
    @staticmethod
    @handle_error
    def process_summary(input_text: str,
                       additional_info: str = "",
                       current_prescription: str = "") -> None:
        """サマリー生成のメインプロセス"""
        ValidationService.validate_inputs(input_text)
        session_params = SummaryService.get_session_parameters()

        result = SummaryService.execute_summary_generation(
            input_text, additional_info, current_prescription, session_params
        )

        SummaryService.handle_generation_result(result, session_params)

    @staticmethod
    def get_session_parameters() -> Dict[str, Any]:
        """セッションパラメーターの取得"""
        return {
            "available_models": getattr(st.session_state, "available_models", []),
            "selected_model": getattr(st.session_state, "selected_model", None),
            "selected_department": getattr(st.session_state, "selected_department", "default"),
            "selected_document_type": getattr(st.session_state, "selected_document_type", "退院時サマリ"),
            "selected_doctor": getattr(st.session_state, "selected_doctor", "default"),
            "model_explicitly_selected": getattr(st.session_state, "model_explicitly_selected", False)
        }

    @staticmethod
    def execute_summary_generation(input_text: str, additional_info: str,
                                 current_prescription: str,
                                 session_params: Dict[str, Any]) -> Dict[str, Any]:
        """サマリー生成の実行"""
        try:
            result = SummaryService.execute_summary_generation_with_ui(
                input_text, additional_info, current_prescription, session_params
            )

            if not result["success"]:
                raise APIError(result['error'])

            return result

        except Exception as e:
            raise APIError(f"作成中にエラーが発生しました: {str(e)}")

    @staticmethod
    def execute_summary_generation_with_ui(input_text: str,
                                         additional_info: str,
                                         current_prescription: str,
                                         session_params: Dict[str, Any]) -> Dict[str, Any]:
        """UI付きでのサマリー生成実行"""
        start_time = datetime.datetime.now()
        status_placeholder = st.empty()
        result_queue = queue.Queue()

        summary_thread = threading.Thread(
            target=GenerationService.generate_summary_task,
            args=(
                input_text,
                session_params["selected_department"],
                session_params["selected_model"],
                result_queue,
                additional_info,
                current_prescription,
                session_params["selected_document_type"],
                session_params["selected_doctor"],
                session_params["model_explicitly_selected"]
            ),
        )
        summary_thread.start()

        GenerationService.display_progress_with_timer(summary_thread, status_placeholder, start_time)

        summary_thread.join()
        status_placeholder.empty()
        result = result_queue.get()

        if result["success"]:
            processing_time = (datetime.datetime.now() - start_time).total_seconds()
            st.session_state.summary_generation_time = processing_time
            result["processing_time"] = processing_time

        return result

    @staticmethod
    def handle_generation_result(result: Dict[str, Any], session_params: Dict[str, Any]) -> None:
        """生成結果の処理"""
        StatisticsService.handle_success_result(result, session_params)


# 後方互換性のためのエイリアス関数
def process_summary(input_text: str,
                   additional_info: str = "",
                   current_prescription: str = "") -> None:
    """後方互換性のためのラッパー関数"""
    return SummaryService.process_summary(input_text, additional_info, current_prescription)
