import datetime
import pytz

import pandas as pd
import streamlit as st

from database.db import get_usage_statistics_repository
from database.repositories import UsageStatisticsRepository
from utils.constants import DOCUMENT_NAME_OPTIONS, MESSAGES, MODEL_OPTIONS
from utils.error_handlers import handle_error
from ui_components.navigation import change_page

JST = pytz.timezone('Asia/Tokyo')

MODEL_MAPPING = {
    "Gemini_Pro": {"pattern": "gemini", "exclude": "flash"},
    "Gemini_Flash": {"pattern": "flash", "exclude": None},
    "Claude": {"pattern": "claude", "exclude": None},
}


@handle_error
def usage_statistics_ui():
    if st.button("作成画面に戻る", key="back_to_main_from_stats"):
        change_page("main")
        st.rerun()

    usage_repo: UsageStatisticsRepository = get_usage_statistics_repository()

    col1, col2 = st.columns(2)

    with col1:
        today = datetime.datetime.now().date()
        start_date = st.date_input("開始日", today - datetime.timedelta(days=7))

    with col2:
        selected_model = st.selectbox("AIモデル", MODEL_OPTIONS, index=0)

    col3, col4 = st.columns(2)

    with col3:
        end_date = st.date_input("終了日", today)

    with col4:
        selected_document_type = st.selectbox("文書名", DOCUMENT_NAME_OPTIONS, index=0)

    start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
    end_datetime = datetime.datetime.combine(end_date, datetime.time.max)

    model_filter = selected_model if selected_model != "すべて" else None
    document_type_filter = selected_document_type if selected_document_type != "すべて" else None

    try:
        total_summary = usage_repo.get_usage_summary(
            start_datetime, end_datetime, model_filter, document_type_filter
        )

        if total_summary["count"] == 0:
            st.info(MESSAGES["NO_DATA_FOUND"])
            return

        dept_statistics = usage_repo.get_department_statistics(
            start_datetime, end_datetime, model_filter, document_type_filter
        )

        usage_records = usage_repo.get_usage_records(
            start_datetime, end_datetime, model_filter, document_type_filter
        )

        dept_data = []
        for stat in dept_statistics:
            dept_name = "全科共通" if stat["department"] == "default" else stat["department"]
            doctor_name = "医師共通" if stat["doctor"] == "default" else stat["doctor"]
            document_types = stat["document_types"] or "不明"

            dept_data.append({
                "文書名": document_types,
                "診療科": dept_name,
                "医師名": doctor_name,
                "作成件数": stat["count"],
                "入力トークン": stat["input_tokens"],
                "出力トークン": stat["output_tokens"],
                "合計トークン": stat["total_tokens"],
            })

        if dept_data:
            dept_df = pd.DataFrame(dept_data)
            st.dataframe(dept_df, hide_index=True)

        detail_data = []
        for record in usage_records:
            model_detail = str(record.model_detail or "").lower()
            model_info = "Gemini_Pro"  # デフォルト

            for model_name, config in MODEL_MAPPING.items():
                pattern = config["pattern"]
                exclude = config["exclude"]

                if pattern in model_detail:
                    if exclude and exclude in model_detail:
                        continue
                    model_info = model_name
                    break

            if record.date.tzinfo:
                jst_date = record.date.astimezone(JST)
            else:
                jst_date = JST.localize(record.date)

            detail_data.append({
                "作成日": jst_date.strftime("%Y/%m/%d"),
                "文書名": record.document_types or "不明",
                "診療科": "全科共通" if record.department == "default" else record.department,
                "医師名": "医師共通" if record.doctor == "default" else record.doctor,
                "AIモデル": model_info,
                "入力トークン": record.input_tokens,
                "出力トークン": record.output_tokens,
                "処理時間(秒)": round(record.processing_time) if record.processing_time else 0,
            })

        if detail_data:
            detail_df = pd.DataFrame(detail_data)
            st.dataframe(detail_df, hide_index=True)

    except Exception as e:
        st.error(f"統計データの取得中にエラーが発生しました: {str(e)}")
        return
