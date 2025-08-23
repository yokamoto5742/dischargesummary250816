import streamlit as st

from services.summary_service import process_summary
from utils.constants import MESSAGES, TAB_NAMES, DOCUMENT_TYPES, DEFAULT_SECTION_NAMES, UIConstants
from utils.error_handlers import handle_error
from ui_components.navigation import render_sidebar
from ui_components.common import UIComponents, SessionManager


def _clear_all_session_data() -> None:
    """セッション状態をクリア"""
    clear_keys = [
        "input_text", "current_prescription", "additional_info",
        "output_summary", "parsed_summary", "summary_generation_time"
    ]
    SessionManager.clear_session_keys(clear_keys)
    
    # 動的に作成されたキーもクリア
    for key in list(st.session_state.keys()):
        if key.startswith("input_text"):
            del st.session_state[key]
    
    # デフォルト値の設定
    SessionManager.update_session_state({
        "clear_input": True,
        "selected_document_type": DOCUMENT_TYPES[0]
    })


def _create_input_areas() -> tuple:
    """入力エリアを作成"""
    current_prescription = UIComponents.create_text_area(
        "退院時処方(現在の処方)",
        height=UIConstants.TEXT_AREA_HEIGHT_SMALL,
        placeholder="処方内容を入力してください...",
        key="current_prescription"
    )

    input_text = UIComponents.create_text_area(
        "カルテ記載",
        height=UIConstants.TEXT_AREA_HEIGHT_SMALL,
        placeholder="カルテテキストを貼り付けてください...",
        key="input_text"
    )

    additional_info = UIComponents.create_text_area(
        "追加情報",
        height=UIConstants.TEXT_AREA_HEIGHT_SMALL,
        placeholder="追加情報を入力してください...",
        key="additional_info"
    )
    
    return current_prescription, input_text, additional_info


def _create_action_buttons(input_text: str, additional_info: str, current_prescription: str) -> None:
    """アクションボタンを作成"""
    def process_callback():
        process_summary(input_text, additional_info, current_prescription)
    
    UIComponents.create_button_pair(
        primary_label="作成",
        secondary_label="テキストをクリア",
        primary_callback=process_callback,
        secondary_callback=_clear_all_session_data
    )


def _create_summary_tabs() -> None:
    """サマリー結果のタブを作成"""
    tabs = st.tabs([
        TAB_NAMES["ALL"],
        TAB_NAMES["ADMISSION_PERIOD"],
        TAB_NAMES["CURRENT_ILLNESS"],
        TAB_NAMES["ADMISSION_TESTS"],
        TAB_NAMES["TREATMENT_PROGRESS"],
        TAB_NAMES["DISCHARGE_NOTES"],
        TAB_NAMES["NOTE"]
    ])

    with tabs[0]:
        UIComponents.create_code_block(
            st.session_state.output_summary,
            height=UIConstants.CODE_BLOCK_HEIGHT_SMALL
        )

    for i, section in enumerate(DEFAULT_SECTION_NAMES, 1):
        with tabs[i]:
            section_content = st.session_state.parsed_summary.get(section, "")
            UIComponents.create_code_block(
                section_content,
                height=UIConstants.CODE_BLOCK_HEIGHT_SMALL
            )


def render_input_section() -> None:
    """入力セクションを描画"""
    # セッション状態の初期化
    SessionManager.initialize_session_state({"clear_input": False})
    
    # 入力エリアの作成
    current_prescription, input_text, additional_info = _create_input_areas()
    
    # アクションボタンの作成
    _create_action_buttons(input_text, additional_info, current_prescription)


def render_summary_results() -> None:
    """サマリー結果を描画"""
    if not st.session_state.output_summary:
        return
    
    if st.session_state.parsed_summary:
        _create_summary_tabs()
    
    # 処理情報の表示
    UIComponents.show_processing_info()


@handle_error
def main_page_app() -> None:
    """メインページアプリケーション"""
    render_sidebar()
    render_input_section()
    render_summary_results()


# 後方互換性のための関数（非推奨）
def clear_inputs():
    """非推奨: _clear_all_session_dataを使用してください"""
    _clear_all_session_data()