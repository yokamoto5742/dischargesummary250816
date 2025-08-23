import streamlit as st
from typing import List, Dict, Any, Optional, Callable
from utils.constants import UIConstants, MESSAGES


class UIComponents:
    """共通UIコンポーネントクラス"""
    
    @staticmethod
    def create_text_area(label: str, 
                        height: int = UIConstants.TEXT_AREA_HEIGHT_SMALL,
                        placeholder: str = "", 
                        key: str = None,
                        value: str = "") -> str:
        """標準化されたテキストエリアを作成"""
        return st.text_area(
            label,
            height=height,
            placeholder=placeholder,
            key=key,
            value=value
        )
    
    @staticmethod
    def create_code_block(content: str, 
                         height: int = UIConstants.CODE_BLOCK_HEIGHT_SMALL,
                         language: str = None) -> None:
        """標準化されたコードブロックを作成"""
        st.code(content, language=language, height=height)
    
    @staticmethod
    def create_button_pair(primary_label: str, 
                          secondary_label: str,
                          primary_callback: Callable = None,
                          secondary_callback: Callable = None,
                          primary_type: str = "primary") -> tuple:
        """2つのボタンを横並びで作成"""
        col1, col2 = st.columns(UIConstants.COLUMNS_TWO)
        
        with col1:
            primary_clicked = st.button(primary_label, type=primary_type)
            if primary_clicked and primary_callback:
                primary_callback()
        
        with col2:
            secondary_clicked = st.button(secondary_label, on_click=secondary_callback)
        
        return primary_clicked, secondary_clicked
    
    @staticmethod
    def create_selectbox_with_mapping(label: str,
                                    options: List[str],
                                    current_value: str,
                                    mapping_func: Callable[[str], str] = None,
                                    key: str = None,
                                    on_change: Callable = None) -> str:
        """マッピング機能付きセレクトボックスを作成"""
        try:
            index = options.index(current_value)
        except ValueError:
            index = 0
        
        return st.selectbox(
            label,
            options,
            index=index,
            format_func=mapping_func,
            key=key,
            on_change=on_change
        )
    
    @staticmethod
    def create_date_range_selector(default_days_back: int = 7) -> tuple:
        """日付範囲選択UIを作成"""
        import datetime
        
        col1, col2 = st.columns(UIConstants.COLUMNS_TWO)
        
        with col1:
            today = datetime.datetime.now().date()
            start_date = st.date_input("開始日", today - datetime.timedelta(days=default_days_back))
        
        with col2:
            end_date = st.date_input("終了日", today)
        
        return start_date, end_date
    
    @staticmethod
    def create_filter_controls(model_options: List[str],
                              document_options: List[str]) -> tuple:
        """フィルター制御UIを作成"""
        col3, col4 = st.columns(UIConstants.COLUMNS_TWO)
        
        with col3:
            selected_model = st.selectbox("AIモデル", model_options, index=0)
        
        with col4:
            selected_document = st.selectbox("文書名", document_options, index=0)
        
        return selected_model, selected_document
    
    @staticmethod
    def show_success_message(message: str) -> None:
        """成功メッセージを表示"""
        st.success(message)
    
    @staticmethod
    def show_error_message(message: str) -> None:
        """エラーメッセージを表示"""
        st.error(message)
    
    @staticmethod
    def show_warning_message(message: str) -> None:
        """警告メッセージを表示"""
        st.warning(message)
    
    @staticmethod
    def show_info_message(message: str) -> None:
        """情報メッセージを表示"""
        st.info(message)
    
    @staticmethod
    def show_processing_info() -> None:
        """処理中の情報メッセージを表示"""
        st.info(MESSAGES["COPY_INSTRUCTION"])
        
        if "summary_generation_time" in st.session_state and st.session_state.summary_generation_time is not None:
            processing_time = st.session_state.summary_generation_time
            st.info(MESSAGES["PROCESSING_TIME"].format(processing_time=processing_time))


class FormComponents:
    """フォーム関連の共通コンポーネント"""
    
    @staticmethod
    def create_form_with_submit(form_key: str, 
                               submit_label: str = "保存",
                               submit_type: str = "primary") -> tuple:
        """フォームと送信ボタンを作成"""
        form = st.form(key=form_key)
        submit_button = form.form_submit_button(submit_label, type=submit_type)
        return form, submit_button
    
    @staticmethod
    def create_department_doctor_selector(departments: List[str], 
                                        doctors_mapping: Dict[str, List[str]],
                                        current_dept: str, 
                                        current_doctor: str,
                                        dept_key: str = "department_selector",
                                        doctor_key: str = "doctor_selector") -> tuple:
        """部門・医師選択UIを作成"""
        col1, col2 = st.columns(UIConstants.COLUMNS_TWO)
        
        with col1:
            selected_dept = UIComponents.create_selectbox_with_mapping(
                "診療科",
                departments,
                current_dept,
                mapping_func=lambda x: "全科共通" if x == "default" else x,
                key=dept_key
            )
        
        available_doctors = doctors_mapping.get(selected_dept, ["default"])
        if current_doctor not in available_doctors:
            current_doctor = available_doctors[0]
        
        with col2:
            selected_doctor = UIComponents.create_selectbox_with_mapping(
                "医師名",
                available_doctors,
                current_doctor,
                mapping_func=lambda x: "医師共通" if x == "default" else x,
                key=doctor_key
            )
        
        return selected_dept, selected_doctor


class NavigationComponents:
    """ナビゲーション関連の共通コンポーネント"""
    
    @staticmethod
    def create_back_button(page_name: str, 
                          button_text: str = "作成画面に戻る",
                          callback: Callable = None) -> bool:
        """戻るボタンを作成"""
        if st.button(button_text, key=f"back_to_{page_name}"):
            if callback:
                callback()
            return True
        return False
    
    @staticmethod
    def create_navigation_buttons(buttons_config: List[Dict[str, Any]]) -> None:
        """複数のナビゲーションボタンを作成"""
        for config in buttons_config:
            if st.button(
                config["label"], 
                key=config.get("key", f"nav_{config['label'].replace(' ', '_')}"),
                type=config.get("type", "secondary")
            ):
                if config.get("callback"):
                    config["callback"]()


class SessionManager:
    """セッション状態管理の共通メソッド"""
    
    @staticmethod
    def initialize_session_state(defaults: Dict[str, Any]) -> None:
        """セッション状態を初期化"""
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    @staticmethod
    def clear_session_keys(keys: List[str]) -> None:
        """指定されたセッションキーをクリア"""
        for key in keys:
            if key in st.session_state:
                del st.session_state[key]
    
    @staticmethod
    def update_session_state(updates: Dict[str, Any]) -> None:
        """セッション状態を一括更新"""
        for key, value in updates.items():
            st.session_state[key] = value