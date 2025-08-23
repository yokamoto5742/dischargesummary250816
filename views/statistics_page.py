import datetime
import pytz
import pandas as pd
import streamlit as st

from database.queries import statistics_queries
from utils.constants import DOCUMENT_NAME_OPTIONS, MESSAGES, StatisticsConstants
from utils.error_handlers import handle_error
from ui_components.navigation import change_page
from ui_components.common import UIComponents, NavigationComponents

JST = pytz.timezone('Asia/Tokyo')


def _convert_dates_to_datetime(start_date: datetime.date, 
                              end_date: datetime.date) -> tuple:
    """日付を日時に変換"""
    start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
    end_datetime = datetime.datetime.combine(end_date, datetime.time.max)
    return start_datetime, end_datetime


def _determine_model_info(model_detail: str) -> str:
    """モデル詳細からモデル情報を決定"""
    model_detail = str(model_detail).lower()
    
    for model_name, config in StatisticsConstants.MODEL_MAPPING.items():
        pattern = config["pattern"]
        exclude = config["exclude"]
        
        if pattern in model_detail:
            if exclude and exclude in model_detail:
                continue
            return model_name
    
    return "Gemini_Pro"  # デフォルト


def _create_filter_section() -> tuple:
    """フィルターセクションを作成"""
    # 日付範囲選択
    start_date, end_date = UIComponents.create_date_range_selector(
        StatisticsConstants.DEFAULT_DAYS_BACK
    )
    
    # モデル・文書タイプ選択
    selected_model, selected_document_type = UIComponents.create_filter_controls(
        StatisticsConstants.MODEL_OPTIONS,
        DOCUMENT_NAME_OPTIONS
    )
    
    return start_date, end_date, selected_model, selected_document_type


def _format_department_summary_data(dept_summary: list) -> list:
    """部門集計データをフォーマット"""
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
    
    return data


def _format_detailed_records_data(records: list) -> list:
    """詳細レコードデータをフォーマット"""
    detail_data = []
    for record in records:
        model_info = _determine_model_info(record.get("model_detail", ""))
        
        # 日時のJST変換
        date_obj = record["date"]
        jst_date = date_obj.astimezone(JST) if date_obj.tzinfo else JST.localize(date_obj)
        
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
    
    return detail_data


def _display_statistics_data(start_datetime: datetime.datetime,
                            end_datetime: datetime.datetime,
                            selected_model: str,
                            selected_document_type: str) -> None:
    """統計データを表示"""
    # 総計データの取得と確認
    total_summary = statistics_queries.get_total_summary(
        start_datetime, end_datetime, selected_model, selected_document_type
    )
    
    if not total_summary or total_summary["count"] == 0:
        UIComponents.show_info_message(MESSAGES["NO_DATA_FOUND"])
        return
    
    # 部門別集計データの取得と表示
    dept_summary = statistics_queries.get_department_summary(
        start_datetime, end_datetime, selected_model, selected_document_type
    )
    
    dept_data = _format_department_summary_data(dept_summary)
    dept_df = pd.DataFrame(dept_data)
    st.dataframe(dept_df, hide_index=True)
    
    # 詳細レコードの取得と表示
    records = statistics_queries.get_detailed_records(
        start_datetime, end_datetime, selected_model, selected_document_type
    )
    
    detail_data = _format_detailed_records_data(records)
    detail_df = pd.DataFrame(detail_data)
    st.dataframe(detail_df, hide_index=True)


@handle_error
def usage_statistics_ui() -> None:
    """使用統計UIのメイン関数"""
    # 戻るボタン
    if NavigationComponents.create_back_button(
        "main_from_stats",
        callback=lambda: change_page("main")
    ):
        st.rerun()
    
    # フィルターセクション
    start_date, end_date, selected_model, selected_document_type = _create_filter_section()
    
    # 日付を日時に変換
    start_datetime, end_datetime = _convert_dates_to_datetime(start_date, end_date)
    
    # 統計データの表示
    _display_statistics_data(
        start_datetime, end_datetime, selected_model, selected_document_type
    )