import streamlit as st

from services.summary_service import process_summary
from utils.constants import MESSAGES, TAB_NAMES, DOCUMENT_TYPES, DOCUMENT_TYPE_TO_PURPOSE_MAPPING
from utils.error_handlers import handle_error
from ui_components.navigation import render_sidebar


def clear_inputs():
    st.session_state.input_text = ""
    st.session_state.current_prescription = ""
    st.session_state.additional_info = ""
    st.session_state.output_summary = ""
    st.session_state.parsed_summary = {}
    st.session_state.summary_generation_time = None
    st.session_state.clear_input = True
    st.session_state.selected_document_type = DOCUMENT_TYPES[0]
    st.session_state.referral_purpose = DOCUMENT_TYPE_TO_PURPOSE_MAPPING.get(DOCUMENT_TYPES[0], "")

    for key in list(st.session_state.keys()):
        if key.startswith("input_text"):
            st.session_state[key] = ""


def render_input_section():
    if "clear_input" not in st.session_state:
        st.session_state.clear_input = False

    referral_purpose = st.text_area(
        "紹介目的",
        height=70,
        key="referral_purpose"
    )

    current_prescription = st.text_area(
        "現在の処方",
        height=70,
        placeholder="現在の処方内容を入力してください...",
        key="current_prescription"
    )

    input_text = st.text_area(
        "カルテ記載",
        height=70,
        placeholder="カルテテキストを貼り付けてください...",
        key="input_text"
    )

    additional_info = st.text_area(
        "追加情報",
        height=70,
        placeholder="追加情報を入力してください...",
        key="additional_info"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("作成", type="primary"):
            process_summary(input_text, additional_info, referral_purpose, current_prescription)

    with col2:
        if st.button("テキストをクリア", on_click=clear_inputs):
            pass


def render_summary_results():
    if st.session_state.output_summary:
        if st.session_state.parsed_summary:
            tabs = st.tabs([
                TAB_NAMES["ALL"],
                TAB_NAMES["MAIN_DISEASE"],
                TAB_NAMES["PURPOSE"],
                TAB_NAMES["HISTORY"],
                TAB_NAMES["SYMPTOMS"],
                TAB_NAMES["TREATMENT"],
                TAB_NAMES["PRESCRIPTION"],
                TAB_NAMES["NOTE"]
            ])

            with tabs[0]:
                st.code(st.session_state.output_summary,
                        language=None,
                        height=150
                        )

            sections = [
                TAB_NAMES["MAIN_DISEASE"],
                TAB_NAMES["PURPOSE"],
                TAB_NAMES["HISTORY"],
                TAB_NAMES["SYMPTOMS"],
                TAB_NAMES["TREATMENT"],
                TAB_NAMES["PRESCRIPTION"],
                TAB_NAMES["NOTE"]
            ]
            for i, section in enumerate(sections, 1):
                with tabs[i]:
                    section_content = st.session_state.parsed_summary.get(section, "")
                    st.code(section_content,
                            language=None,
                            height=150)

        st.info(MESSAGES["COPY_INSTRUCTION"])

        if "summary_generation_time" in st.session_state and st.session_state.summary_generation_time is not None:
            processing_time = st.session_state.summary_generation_time
            st.info(MESSAGES["PROCESSING_TIME"].format(processing_time=processing_time))


@handle_error
def main_page_app():
    render_sidebar()
    render_input_section()
    render_summary_results()
