import datetime
import pytz

import pandas as pd
import streamlit as st

from database.db import DatabaseManager
from utils.constants import DOCUMENT_TYPE_OPTIONS, MESSAGES
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

    db_manager = DatabaseManager.get_instance()

    col1, col2 = st.columns(2)

    with col1:
        today = datetime.datetime.now().date()
        start_date = st.date_input("開始日", today - datetime.timedelta(days=7))

    with col2:
        models = ["すべて", "Claude", "Gemini_Pro", "Gemini_Flash"]
        selected_model = st.selectbox("AIモデル", models, index=0)

    col3, col4 = st.columns(2)

    with col3:
        end_date = st.date_input("終了日", today)

    with col4:
        selected_document_type = st.selectbox("文書名", DOCUMENT_TYPE_OPTIONS, index=0)

    start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
    end_datetime = datetime.datetime.combine(end_date, datetime.time.max)

    query_conditions = []
    query_params = {
        "start_date": start_datetime,
        "end_date": end_datetime
    }

    query_conditions.append("date >= :start_date AND date <= :end_date")

    if selected_model != "すべて":
        model_config = MODEL_MAPPING.get(selected_model)
        if model_config:
            query_conditions.append("model_detail ILIKE :model_pattern")
            query_params["model_pattern"] = f"%{model_config['pattern']}%"

            if model_config["exclude"]:
                query_conditions.append("model_detail NOT ILIKE :model_exclude")
                query_params["model_exclude"] = f"%{model_config['exclude']}%"

    if selected_document_type != "すべて":
        if selected_document_type == "不明":
            query_conditions.append("document_types IS NULL")
        else:
            query_conditions.append("document_types = :doc_type")
            query_params["doc_type"] = selected_document_type

    where_clause = " AND ".join(query_conditions)

    total_query = f"""
    SELECT
        COUNT(*) as count,
        SUM(input_tokens) as total_input_tokens,
        SUM(output_tokens) as total_output_tokens,
        SUM(total_tokens) as total_tokens
    FROM summary_usage
    WHERE {where_clause}
    """

    total_summary = db_manager.execute_query(total_query, query_params)

    if not total_summary or total_summary[0]["count"] == 0:
        st.info(MESSAGES["NO_DATA_FOUND"])
        return

    dept_query = f"""
    SELECT
        COALESCE(department, 'default') as department,
        COALESCE(doctor, 'default') as doctor,
        document_types,
        COUNT(*) as count,
        SUM(input_tokens) as input_tokens,
        SUM(output_tokens) as output_tokens,
        SUM(total_tokens) as total_tokens,
        SUM(processing_time) as processing_time
    FROM summary_usage
    WHERE {where_clause}
    GROUP BY department, doctor, document_types
    ORDER BY count DESC
    """

    dept_summary = db_manager.execute_query(dept_query, query_params)

    records_query = f"""
    SELECT
        date,
        document_types,
        model_detail,
        department,
        doctor,
        input_tokens,
        output_tokens,
        processing_time
    FROM summary_usage
    WHERE {where_clause}
    ORDER BY date DESC
    """

    records = db_manager.execute_query(records_query, query_params)

    data = []
    for stat in dept_summary:
        dept_name = "全科共通" if stat["department"] == "default" else stat["department"]
        doctor_name = "医師共通" if stat["doctor"] == "default" else stat["doctor"]
        document_types = stat["document_types"] or "不明"
        data.append({
            "文書名": document_types,
            "診療科": dept_name,
            "医師名": doctor_name,
            "作成件数": stat["count"],
            "入力トークン": stat["input_tokens"],
            "出力トークン": stat["output_tokens"],
            "合計トークン": stat["total_tokens"],
        })

    df = pd.DataFrame(data)
    st.dataframe(df, hide_index=True)

    detail_data = []
    for record in records:
        model_detail = str(record.get("model_detail", "")).lower()
        model_info = "Gemini_Pro"

        for model_name, config in MODEL_MAPPING.items():
            pattern = config["pattern"]
            exclude = config["exclude"]

            if pattern in model_detail:
                if exclude and exclude in model_detail:
                    continue
                model_info = model_name
                break

        jst_date = record["date"].astimezone(JST) if record["date"].tzinfo else JST.localize(record["date"])

        detail_data.append({
            "作成日": jst_date.strftime("%Y/%m/%d"),
            "文書名": record.get("document_types") or "不明",
            "診療科": "全科共通" if record.get("department") == "default" else record.get("department"),
            "医師名": "医師共通" if record.get("doctor") == "default" else record.get("doctor"),
            "AIモデル": model_info,
            "入力トークン": record["input_tokens"],
            "出力トークン": record["output_tokens"],
            "処理時間(秒)": round(record["processing_time"]),
        })

    detail_df = pd.DataFrame(detail_data)
    st.dataframe(detail_df, hide_index=True)
