import streamlit as st

from utils.constants import DEPARTMENT_DOCTORS_MAPPING, DOCUMENT_TYPES, DEFAULT_DOCUMENT_TYPE, UIConstants
from utils.error_handlers import handle_error
from utils.exceptions import AppError
from utils.prompt_manager import get_all_departments, get_prompt, create_or_update_prompt, delete_prompt
from utils.config import get_config
from ui_components.navigation import change_page
from ui_components.common import UIComponents, FormComponents, NavigationComponents, SessionManager


def _initialize_session_defaults() -> None:
    """セッション状態のデフォルト値を初期化"""
    defaults = {
        "selected_dept_for_prompt": "default",
        "selected_doc_type_for_prompt": DEFAULT_DOCUMENT_TYPE,
        "selected_doctor_for_prompt": "default",
        "document_model_mapping": {},
        "update_ui": False  # 追加
    }
    SessionManager.initialize_session_state(defaults)


def _update_document_model_mapping(selected_doc_type: str) -> None:
    """文書タイプ変更時のモデルマッピング更新"""
    prompt_data = get_prompt(
        st.session_state.selected_dept_for_prompt,
        selected_doc_type,
        st.session_state.selected_doctor_for_prompt
    )

    if prompt_data and prompt_data.get("selected_model"):
        st.session_state.document_model_mapping[selected_doc_type] = prompt_data.get("selected_model")

    st.session_state.update_ui = True


def _handle_department_change() -> None:
    """部門変更の処理"""
    if "prompt_department_selector" not in st.session_state:
        return

    st.session_state.selected_dept_for_prompt = st.session_state.prompt_department_selector

    available_doctors = DEPARTMENT_DOCTORS_MAPPING.get(
        st.session_state.selected_dept_for_prompt, ["default"]
    )
    if st.session_state.selected_doctor_for_prompt not in available_doctors:
        st.session_state.selected_doctor_for_prompt = available_doctors[0]

    st.session_state.update_ui = True


def _handle_document_type_change() -> None:
    """文書タイプ変更の処理"""
    if "prompt_document_type_selector" not in st.session_state:
        return

    new_doc_type = st.session_state.prompt_document_type_selector
    st.session_state.selected_doc_type_for_prompt = new_doc_type
    _update_document_model_mapping(new_doc_type)


def _handle_doctor_change() -> None:
    """医師変更の処理"""
    if "prompt_doctor_selector" not in st.session_state:
        return

    st.session_state.selected_doctor_for_prompt = st.session_state.prompt_doctor_selector
    st.session_state.update_ui = True


def _get_available_options() -> tuple:
    """利用可能なオプションを取得"""
    departments = ["default"] + get_all_departments()
    document_types = DOCUMENT_TYPES if DOCUMENT_TYPES else [DEFAULT_DOCUMENT_TYPE]
    return departments, document_types


def _create_selection_controls() -> tuple:
    """選択制御UIを作成"""
    departments, document_types = _get_available_options()
    
    col1, col2 = st.columns(UIConstants.COLUMNS_TWO)
    
    with col1:
        selected_doc_type = UIComponents.create_selectbox_with_mapping(
            "文書名",
            document_types,
            st.session_state.selected_doc_type_for_prompt,
            key="prompt_document_type_selector",
            on_change=_handle_document_type_change
        )
    
    col3, col4 = st.columns(UIConstants.COLUMNS_TWO)
    
    with col3:
        selected_dept = UIComponents.create_selectbox_with_mapping(
            "診療科",
            departments,
            st.session_state.selected_dept_for_prompt,
            mapping_func=lambda x: "全科共通" if x == "default" else x,
            key="prompt_department_selector",
            on_change=_handle_department_change
        )
    
    available_doctors = DEPARTMENT_DOCTORS_MAPPING.get(selected_dept, ["default"])
    if st.session_state.selected_doctor_for_prompt not in available_doctors:
        st.session_state.selected_doctor_for_prompt = available_doctors[0]
    
    with col4:
        selected_doctor = UIComponents.create_selectbox_with_mapping(
            "医師名",
            available_doctors,
            st.session_state.selected_doctor_for_prompt,
            mapping_func=lambda x: "医師共通" if x == "default" else x,
            key="prompt_doctor_selector",
            on_change=_handle_doctor_change
        )
    
    # セッション状態の更新
    SessionManager.update_session_state({
        "selected_dept_for_prompt": selected_dept,
        "selected_doc_type_for_prompt": selected_doc_type,
        "selected_doctor_for_prompt": selected_doctor
    })
    
    return selected_dept, selected_doc_type, selected_doctor


def _create_model_selector(selected_doc_type: str) -> str:
    """AIモデル選択UIを作成"""
    available_models = getattr(st.session_state, "available_models", [])

    # available_modelsが空の場合は早期リターン
    if not available_models:
        st.warning("利用可能なAIモデルがありません。環境変数を確認してください。")
        return None

    # document_model_mappingが存在しない場合は初期化
    if "document_model_mapping" not in st.session_state:
        st.session_state.document_model_mapping = {}

    # 現在選択されているモデルを決定
    prompt_data = get_prompt(
        st.session_state.selected_dept_for_prompt,
        selected_doc_type,
        st.session_state.selected_doctor_for_prompt
    )

    if prompt_data and prompt_data.get("selected_model"):
        selected_model = prompt_data.get("selected_model")
    elif selected_doc_type in st.session_state.document_model_mapping:
        selected_model = st.session_state.document_model_mapping[selected_doc_type]
    else:
        selected_model = available_models[0]

    st.session_state.document_model_mapping[selected_doc_type] = selected_model

    model_index = 0
    if selected_model in available_models:
        model_index = available_models.index(selected_model)

    col1, col2 = st.columns(UIConstants.COLUMNS_TWO)
    with col2:
        # コールバック関数を削除してシンプルにする
        prompt_model = st.selectbox(
            "AIモデル",
            available_models,
            index=model_index,
            key=f"prompt_model_{selected_doc_type}"
        )

    # セッション状態を直接更新
    st.session_state.document_model_mapping[selected_doc_type] = prompt_model
    return prompt_model


def _create_prompt_form(selected_dept: str, selected_doc_type: str, 
                       selected_doctor: str, prompt_model: str) -> None:
    """プロンプト編集フォームを作成"""
    config = get_config()
    default_prompt_content = config['PROMPTS']['summary']
    
    form_key = f"edit_prompt_form_{selected_dept}_{selected_doc_type}_{selected_doctor}"
    
    with st.form(key=form_key):
        # プロンプト内容の取得
        prompt_data = get_prompt(selected_dept, selected_doc_type, selected_doctor)
        content_value = prompt_data.get("content", "") if prompt_data else default_prompt_content.replace('\\n', '\n')
        
        # プロンプト編集エリア
        prompt_content = UIComponents.create_text_area(
            "プロンプト内容",
            height=UIConstants.TEXT_AREA_HEIGHT_LARGE,
            value=content_value,
            key=f"prompt_content_{selected_dept}_{selected_doc_type}_{selected_doctor}"
        )
        
        # 送信ボタン
        submit = st.form_submit_button("保存")
        
        if submit:
            _handle_prompt_save(
                selected_dept, selected_doc_type, selected_doctor,
                prompt_content, prompt_model
            )


def _handle_prompt_save(dept: str, doc_type: str, doctor: str, 
                       content: str, model: str) -> None:
    """プロンプト保存の処理"""
    if model:
        st.session_state.document_model_mapping[doc_type] = model

    success, message = create_or_update_prompt(dept, doc_type, doctor, content, model)

    if success:
        st.session_state.success_message = message
        st.rerun()
    else:
        raise AppError(message)


def _create_delete_button(selected_dept: str, selected_doc_type: str, 
                         selected_doctor: str) -> None:
    """削除ボタンを作成"""
    if (selected_dept != "default" or 
        selected_doc_type != DEFAULT_DOCUMENT_TYPE or 
        selected_doctor != "default"):
        
        delete_key = f"delete_prompt_{selected_dept}_{selected_doc_type}_{selected_doctor}"
        
        if st.button("プロンプトを削除", key=delete_key, type="primary"):
            _handle_prompt_delete(selected_dept, selected_doc_type, selected_doctor)


def _handle_prompt_delete(dept: str, doc_type: str, doctor: str) -> None:
    """プロンプト削除の処理"""
    success, message = delete_prompt(dept, doc_type, doctor)
    
    if success:
        st.session_state.success_message = message
        # デフォルト値にリセット
        SessionManager.update_session_state({
            "selected_dept_for_prompt": "default",
            "selected_doc_type_for_prompt": DEFAULT_DOCUMENT_TYPE,
            "selected_doctor_for_prompt": "default"
        })
        st.rerun()
    else:
        raise AppError(message)


def _display_success_message() -> None:
    """成功メッセージの表示"""
    if st.session_state.success_message:
        UIComponents.show_success_message(st.session_state.success_message)
        st.session_state.success_message = None


@handle_error
def prompt_management_ui() -> None:
    """プロンプト管理UIのメイン関数"""
    # セッション状態の初期化
    _initialize_session_defaults()

    # 成功メッセージの表示
    _display_success_message()

    # 戻るボタン
    NavigationComponents.create_back_button(
        "main",
        callback=lambda: change_page("main")
    )

    # 選択制御UIの作成
    selected_dept, selected_doc_type, selected_doctor = _create_selection_controls()

    # AIモデル選択UIの作成
    prompt_model = _create_model_selector(selected_doc_type)

    # prompt_modelがNoneの場合は処理を中断
    if prompt_model is None:
        return

    # プロンプト編集フォームの作成
    _create_prompt_form(selected_dept, selected_doc_type, selected_doctor, prompt_model)

    # 削除ボタンの作成
    _create_delete_button(selected_dept, selected_doc_type, selected_doctor)
