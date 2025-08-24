import datetime
from typing import Dict, Any

import pytz
import streamlit as st

from database.db import get_usage_statistics_repository
from database.repositories import UsageStatisticsRepository
from utils.constants import APP_TYPE

JST = pytz.timezone('Asia/Tokyo')


class StatisticsService:
    
    @staticmethod
    def save_usage_to_database(result: Dict[str, Any],
                             session_params: Dict[str, Any]) -> None:
        try:
            usage_repo: UsageStatisticsRepository = get_usage_statistics_repository()
            now_jst = datetime.datetime.now().astimezone(JST)

            usage_data = {
                "date": now_jst,
                "app_type": APP_TYPE,
                "document_types": session_params["selected_document_type"],
                "model_detail": result["model_detail"],
                "department": session_params["selected_department"],
                "doctor": session_params["selected_doctor"],
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "total_tokens": result["input_tokens"] + result["output_tokens"],
                "processing_time": round(result["processing_time"])
            }

            usage_repo.save_usage(usage_data)

        except Exception as db_error:
            st.warning(f"データベース保存中にエラーが発生しました: {str(db_error)}")

    @staticmethod
    def handle_success_result(result: Dict[str, Any],
                            session_params: Dict[str, Any]) -> None:
        st.session_state.output_summary = result["output_summary"]
        st.session_state.parsed_summary = result["parsed_summary"]

        if result.get("model_switched"):
            st.info(f"⚠️ 入力テキストが長いため{result['original_model']} からGemini_Proに切り替えました")

        StatisticsService.save_usage_to_database(result, session_params)
