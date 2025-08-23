import streamlit as st

from utils.constants import DEPARTMENT_DOCTORS_MAPPING, DOCUMENT_TYPES, DEFAULT_DOCUMENT_TYPE
from utils.error_handlers import handle_error
from utils.exceptions import AppError
from utils.prompt_manager import get_all_departments, get_prompt, create_or_update_prompt, delete_prompt
from utils.config import get_config
from ui_components.navigation import change_page


def update_document_type():
    """文書タイプ変更時の処理"""
    st.session_state.selected_doc_type_for_prompt = st.session_state.prompt_document_type_selector

    prompt_data = get_prompt(
        st.session_state.selected_dept_for_prompt,
        st.session_state.selected_doc_type_for_prompt,
        st.session_state.selected_doctor_for_prompt
    )

    if prompt_data and prompt_data.get("selected_model"):
        st.session_state.document_model_mapping[st.session_state.selected_doc_type_for_prompt] = prompt_data.get(
            "selected_model")

    st.session_state.update_ui = True


def update_department():
    """診療科変更時の処理"""
    st.session_state.selected_dept_for_prompt = st.session_state.prompt_department_selector

    available_doctors = DEPARTMENT_DOCTORS_MAPPING.get(st.session_state.selected_dept_for_prompt, ["default"])
    if st.session_state.selected_doctor_for_prompt not in available_doctors:
        st.session_state.selected_doctor_for_prompt = available_doctors[0]

    st.session_state.update_ui = True


def update_doctor():
    """医師変更時の処理"""
    st.session_state.selected_doctor_for_prompt = st.session_state.prompt_doctor_selector
    st.session_state.update_ui = True


def initialize_session_state():
    """セッション状態の初期化"""
    if "selected_dept_for_prompt" not in st.session_state:
        st.session_state.selected_dept_for_prompt = "default"

    if "selected_doc_type_for_prompt" not in st.session_state:
        st.session_state.selected_doc_type_for_prompt = DEFAULT_DOCUMENT_TYPE

    if "selected_doctor_for_prompt" not in st.session_state:
        st.session_state.selected_doctor_for_prompt = "default"

    if "document_model_mapping" not in st.session_state:
        st.session_state.document_model_mapping = {}


def render_navigation():
    """ナビゲーション部分の描画"""
    if st.session_state.success_message:
        st.success(st.session_state.success_message)
        st.session_state.success_message = None

    if st.button("作成画面に戻る", key="back_to_main"):
        change_page("main")
        st.rerun()


def get_selection_options():
    """選択肢のデータを取得"""
    departments = ["default"] + get_all_departments()
    document_types = DOCUMENT_TYPES if DOCUMENT_TYPES else [DEFAULT_DOCUMENT_TYPE]
    available_models = getattr(st.session_state, "available_models", [])

    return departments, document_types, available_models


def render_document_type_selector(document_types):
    """文書タイプセレクターの描画"""
    return st.selectbox(
        "文書名",
        document_types,
        index=document_types.index(
            st.session_state.selected_doc_type_for_prompt
        ) if st.session_state.selected_doc_type_for_prompt in document_types else 0,
        key="prompt_document_type_selector",
        on_change=update_document_type
    )


def render_department_selector(departments):
    """診療科セレクターの描画"""
    return st.selectbox(
        "診療科",
        departments,
        index=departments.index(
            st.session_state.selected_dept_for_prompt
        ) if st.session_state.selected_dept_for_prompt in departments else 0,
        format_func=lambda x: "全科共通" if x == "default" else x,
        key="prompt_department_selector",
        on_change=update_department
    )


def render_doctor_selector(selected_dept):
    """医師セレクターの描画"""
    available_doctors = DEPARTMENT_DOCTORS_MAPPING.get(selected_dept, ["default"])
    if st.session_state.selected_doctor_for_prompt not in available_doctors:
        st.session_state.selected_doctor_for_prompt = available_doctors[0]

    return st.selectbox(
        "医師名",
        available_doctors,
        index=available_doctors.index(st.session_state.selected_doctor_for_prompt),
        format_func=lambda x: "医師共通" if x == "default" else x,
        key="prompt_doctor_selector",
        on_change=update_doctor
    )


def get_selected_model(prompt_data, selected_doc_type, available_models):
    """選択されたモデルを決定"""
    if prompt_data and prompt_data.get("selected_model"):
        return prompt_data.get("selected_model")
    elif selected_doc_type in st.session_state.document_model_mapping:
        return st.session_state.document_model_mapping[selected_doc_type]
    else:
        return available_models[0] if available_models else None


def render_model_selector(available_models, selected_model, selected_doc_type):
    """AIモデルセレクターの描画"""
    model_index = 0
    if selected_model in available_models:
        model_index = available_models.index(selected_model)

    def update_model_mapping():
        prompt_model = st.session_state[f"prompt_model_{selected_doc_type}"]
        st.session_state.document_model_mapping[selected_doc_type] = prompt_model

    return st.selectbox(
        "AIモデル",
        available_models,
        index=model_index,
        key=f"prompt_model_{selected_doc_type}",
        on_change=update_model_mapping
    )


def render_selectors():
    """セレクター群の描画"""
    departments, document_types, available_models = get_selection_options()

    col1, col2 = st.columns(2)
    with col1:
        selected_doc_type = render_document_type_selector(document_types)

    col3, col4 = st.columns(2)
    with col3:
        selected_dept = render_department_selector(departments)

    with col4:
        selected_doctor = render_doctor_selector(selected_dept)

    # セッション状態を更新
    st.session_state.selected_dept_for_prompt = selected_dept
    st.session_state.selected_doc_type_for_prompt = selected_doc_type
    st.session_state.selected_doctor_for_prompt = selected_doctor

    # プロンプトデータを取得してモデルを決定
    prompt_data = get_prompt(selected_dept, selected_doc_type, selected_doctor)
    selected_model = get_selected_model(prompt_data, selected_doc_type, available_models)
    st.session_state.document_model_mapping[selected_doc_type] = selected_model

    with col2:
        prompt_model = render_model_selector(available_models, selected_model, selected_doc_type)

    st.session_state.document_model_mapping[selected_doc_type] = prompt_model

    return selected_dept, selected_doc_type, selected_doctor, prompt_data, prompt_model


def get_prompt_content(prompt_data):
    """プロンプト内容を取得"""
    if prompt_data:
        return prompt_data.get("content", "")
    else:
        config = get_config()
        return config['PROMPTS']['summary'].replace('\\n', '\n')


def handle_prompt_save(selected_dept, selected_doc_type, selected_doctor,
                       prompt_content, prompt_model):
    """プロンプト保存処理"""
    if prompt_model:
        st.session_state.document_model_mapping[selected_doc_type] = prompt_model

    success, message = create_or_update_prompt(
        selected_dept,
        selected_doc_type,
        selected_doctor,
        prompt_content,
        prompt_model
    )

    if success:
        st.session_state.success_message = message
        st.rerun()
    else:
        raise AppError(message)


def render_prompt_form(selected_dept, selected_doc_type, selected_doctor,
                       prompt_data, prompt_model):
    """プロンプト編集フォームの描画"""
    with st.form(key=f"edit_prompt_form_{selected_dept}_{selected_doc_type}_{selected_doctor}"):
        content_value = get_prompt_content(prompt_data)

        prompt_content = st.text_area(
            "プロンプト内容",
            value=content_value,
            height=200,
            key=f"prompt_content_{selected_dept}_{selected_doc_type}_{selected_doctor}"
        )

        submit = st.form_submit_button("保存")

        if submit:
            handle_prompt_save(
                selected_dept, selected_doc_type, selected_doctor,
                prompt_content, prompt_model
            )


def handle_prompt_deletion(selected_dept, selected_doc_type, selected_doctor):
    """プロンプト削除処理"""
    success, message = delete_prompt(selected_dept, selected_doc_type, selected_doctor)
    if success:
        st.session_state.success_message = message
        st.session_state.selected_dept_for_prompt = "default"
        st.session_state.selected_doc_type_for_prompt = DEFAULT_DOCUMENT_TYPE
        st.session_state.selected_doctor_for_prompt = "default"
        st.rerun()
    else:
        raise AppError(message)


def render_delete_button(selected_dept, selected_doc_type, selected_doctor):
    """削除ボタンの描画"""
    # デフォルトプロンプトは削除不可
    if (selected_dept != "default" or
            selected_doc_type != DEFAULT_DOCUMENT_TYPE or
            selected_doctor != "default"):

        if st.button(
                "プロンプトを削除",
                key=f"delete_prompt_{selected_dept}_{selected_doc_type}_{selected_doctor}",
                type="primary"
        ):
            handle_prompt_deletion(selected_dept, selected_doc_type, selected_doctor)


@handle_error
def prompt_management_ui():
    """プロンプト管理UI のメイン関数"""
    initialize_session_state()
    render_navigation()

    selected_dept, selected_doc_type, selected_doctor, prompt_data, prompt_model = render_selectors()

    render_prompt_form(selected_dept, selected_doc_type, selected_doctor,
                       prompt_data, prompt_model)

    render_delete_button(selected_dept, selected_doc_type, selected_doctor)
