import streamlit as st

from database.db import DatabaseManager
from utils.config import CLAUDE_API_KEY, GEMINI_CREDENTIALS, GEMINI_FLASH_MODEL, GEMINI_MODEL
from utils.constants import APP_TYPE, DEFAULT_DEPARTMENT, DOCUMENT_TYPES, DEPARTMENT_DOCTORS_MAPPING, \
    DEFAULT_DOCUMENT_TYPE, DOCUMENT_TYPE_TO_PURPOSE_MAPPING
from utils.prompt_manager import get_prompt


def change_page(page):
    st.session_state.current_page = page


def update_document_model():
    selected_dept = st.session_state.selected_department
    selected_doctor = st.session_state.selected_doctor
    new_doc_type = st.session_state.document_type_selector

    st.session_state.selected_document_type = new_doc_type
    st.session_state.model_explicitly_selected = False

    default_purpose = DOCUMENT_TYPE_TO_PURPOSE_MAPPING.get(new_doc_type, "")
    st.session_state.referral_purpose = default_purpose

    prompt_data = get_prompt(selected_dept, new_doc_type, selected_doctor)
    if prompt_data and prompt_data.get("selected_model") in st.session_state.available_models:
        st.session_state.selected_model = prompt_data.get("selected_model")
    elif "available_models" in st.session_state and st.session_state.available_models:
        if "Gemini_Pro" in st.session_state.available_models:
            st.session_state.selected_model = "Gemini_Pro"
        else:
            st.session_state.selected_model = st.session_state.available_models[0]


def render_sidebar():
    departments = ["default"] + [dept for dept in DEFAULT_DEPARTMENT if dept != "default"]
    previous_dept = st.session_state.selected_department
    previous_model = getattr(st.session_state, "selected_model", None)
    previous_doctor = getattr(st.session_state, "selected_doctor", None)

    try:
        index = departments.index(st.session_state.selected_department)
    except ValueError:
        index = 0
        st.session_state.selected_department = departments[0]

    if len(departments) > 1:
        selected_dept = st.sidebar.selectbox(
            "診療科",
            departments,
            index=index,
            format_func=lambda x: "全科共通" if x == "default" else x,
            key="department_selector"
        )
        st.session_state.selected_department = selected_dept
    else:
        st.session_state.selected_department = departments[0]
        selected_dept = departments[0]

    available_doctors = DEPARTMENT_DOCTORS_MAPPING.get(selected_dept, ["default"])

    if "selected_doctor" not in st.session_state or st.session_state.selected_doctor not in available_doctors:
        st.session_state.selected_doctor = available_doctors[0]

    if selected_dept != previous_dept:
        if selected_dept == "default":
            st.session_state.selected_doctor = "default"
        else:
            st.session_state.selected_doctor = available_doctors[0]

        save_user_settings(selected_dept, st.session_state.selected_model, st.session_state.selected_doctor)
        st.rerun()

    if len(available_doctors) > 1:
        selected_doctor = st.sidebar.selectbox(
            "医師名",
            available_doctors,
            index=available_doctors.index(st.session_state.selected_doctor),
            format_func=lambda x: "医師共通" if x == "default" else x,
            key="doctor_selector"
        )
        if selected_doctor != previous_doctor:
            st.session_state.selected_doctor = selected_doctor
            save_user_settings(st.session_state.selected_department, st.session_state.selected_model, selected_doctor)
    else:
        st.session_state.selected_doctor = available_doctors[0]
        selected_doctor = available_doctors[0]

    document_types = DOCUMENT_TYPES

    if "selected_document_type" not in st.session_state:
        st.session_state.selected_document_type = document_types[0] if document_types else DEFAULT_DOCUMENT_TYPE
        if "referral_purpose" not in st.session_state:
            st.session_state.referral_purpose = DOCUMENT_TYPE_TO_PURPOSE_MAPPING.get(
                st.session_state.selected_document_type, "")

    if len(document_types) > 1:
        selected_document_type = st.sidebar.selectbox(
            "文書名",
            document_types,
            index=document_types.index(
                st.session_state.selected_document_type) if st.session_state.selected_document_type in document_types else 0,
            key="document_type_selector",
            on_change=update_document_model
        )
    else:
        st.session_state.selected_document_type = document_types[0]
        selected_document_type = document_types[0]

    st.session_state.available_models = []
    if GEMINI_MODEL and GEMINI_CREDENTIALS:
        st.session_state.available_models.append("Gemini_Pro")
    if GEMINI_FLASH_MODEL and GEMINI_CREDENTIALS:
        st.session_state.available_models.append("Gemini_Flash")
    if CLAUDE_API_KEY:
        st.session_state.available_models.append("Claude")

    if len(st.session_state.available_models) > 1:
        if "selected_model" not in st.session_state:
            if "Gemini_Pro" in st.session_state.available_models:
                default_model = "Gemini_Pro"
            else:
                default_model = st.session_state.available_models[0]
            st.session_state.selected_model = default_model

        try:
            model_index = st.session_state.available_models.index(st.session_state.selected_model)
        except (ValueError, AttributeError):
            model_index = 0
            if st.session_state.available_models:
                st.session_state.selected_model = st.session_state.available_models[0]

        selected_model = st.sidebar.selectbox(
            "AIモデル",
            st.session_state.available_models,
            index=model_index,
            key="model_selector"
        )

        if selected_model != previous_model:
            st.session_state.selected_model = selected_model
            st.session_state.model_explicitly_selected = True
            save_user_settings(st.session_state.selected_department, st.session_state.selected_model,
                               st.session_state.selected_doctor)

    elif len(st.session_state.available_models) == 1:
        st.session_state.selected_model = st.session_state.available_models[0]
        st.session_state.model_explicitly_selected = False

    st.sidebar.markdown("・入力および出力テキストは保存されません")
    st.sidebar.markdown("・出力結果は必ず確認してください")

    if st.sidebar.button("プロンプト管理", key="sidebar_prompt_management"):
        change_page("prompt_edit")
        st.rerun()

    if st.sidebar.button("統計情報", key="sidebar_usage_statistics"):
        change_page("statistics")
        st.rerun()


def save_user_settings(department, model,
                       doctor="default",
                       document_type=DEFAULT_DOCUMENT_TYPE):
    try:
        if department != "default" and department not in DEFAULT_DEPARTMENT:
            department = "default"
        db_manager = DatabaseManager.get_instance()

        setting_id = f"user_preferences_{APP_TYPE}"

        query = """
                INSERT INTO app_settings
                (setting_id, app_type, selected_department, selected_model,
                 selected_document_type, selected_doctor, updated_at)
                VALUES (:setting_id, :app_type, 
                        :department, :model,
                        :document_type, :doctor, 
                        CURRENT_TIMESTAMP) 
                ON CONFLICT (setting_id) 
                DO UPDATE SET
                    app_type = EXCLUDED.app_type,
                    selected_department = EXCLUDED.selected_department,
                    selected_model = EXCLUDED.selected_model,
                    selected_document_type = EXCLUDED.selected_document_type,
                    selected_doctor = EXCLUDED.selected_doctor,
                    updated_at = CURRENT_TIMESTAMP
                """

        db_manager.execute_query(query, {
            "setting_id": setting_id,
            "app_type": APP_TYPE,
            "department": department,
            "model": model,
            "document_type": document_type,
            "doctor": doctor
        }, fetch=False)

    except Exception as e:
        print(f"設定の保存に失敗しました: {str(e)}")


def load_user_settings():
    try:
        from utils.constants import APP_TYPE

        db_manager = DatabaseManager.get_instance()
        setting_id = f"user_preferences_{APP_TYPE}"

        query = """
                SELECT selected_department, selected_model, selected_document_type, selected_doctor
                FROM app_settings
                WHERE setting_id = :setting_id
                """
        settings = db_manager.execute_query(query, {"setting_id": setting_id})

        if settings:
            return (settings[0]["selected_department"],
                    settings[0]["selected_model"],
                    settings[0].get("selected_document_type", DEFAULT_DOCUMENT_TYPE),
                    settings[0].get("selected_doctor", "default"))
        return None, None, None, None
    except Exception as e:
        print(f"設定の読み込みに失敗しました: {str(e)}")
        return None, None, None, None
