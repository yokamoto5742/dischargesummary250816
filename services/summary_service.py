import datetime
import queue
import threading
import time
from typing import Dict, Any, Tuple

import pytz
import streamlit as st

from database.db import DatabaseManager
from external_service.api_factory import generate_summary
from utils.config import (CLAUDE_API_KEY, CLAUDE_MODEL,
                          GEMINI_CREDENTIALS, GEMINI_FLASH_MODEL, GEMINI_MODEL,
                          MAX_INPUT_TOKENS, MIN_INPUT_TOKENS,MAX_TOKEN_THRESHOLD
                          )
from utils.constants import (APP_TYPE, MESSAGES, DEFAULT_DEPARTMENT, DEFAULT_DOCUMENT_TYPE, 
                           DOCUMENT_TYPES, SystemConstants)
from utils.error_handlers import handle_error
from utils.exceptions import APIError
from utils.prompt_manager import get_prompt
from utils.text_processor import format_output_summary, parse_output_summary

JST = pytz.timezone('Asia/Tokyo')


def _validate_inputs(input_text: str) -> None:
    """入力テキストの妥当性をチェック"""
    if not input_text:
        st.warning(MESSAGES["NO_INPUT"])
        return

    input_length = len(input_text.strip())
    if input_length < MIN_INPUT_TOKENS:
        st.warning(f"{MESSAGES['INPUT_TOO_SHORT']}")
        return

    if input_length > MAX_INPUT_TOKENS:
        st.warning(f"{MESSAGES['INPUT_TOO_LONG']}")
        return


def _validate_api_credentials() -> None:
    """API認証情報の存在をチェック"""
    if not any([GEMINI_CREDENTIALS, CLAUDE_API_KEY]):
        raise APIError(MESSAGES["NO_API_CREDENTIALS"])


def _get_session_parameters() -> Dict[str, Any]:
    """セッション状態からパラメータを取得"""
    return {
        "available_models": getattr(st.session_state, "available_models", []),
        "selected_model": getattr(st.session_state, "selected_model", None),
        "selected_department": getattr(st.session_state, "selected_department", "default"),
        "selected_document_type": getattr(st.session_state, "selected_document_type", DEFAULT_DOCUMENT_TYPE),
        "selected_doctor": getattr(st.session_state, "selected_doctor", "default"),
        "model_explicitly_selected": getattr(st.session_state, "model_explicitly_selected", False)
    }


def _normalize_parameters(department: str, document_type: str) -> Tuple[str, str]:
    """部門と文書タイプの正規化"""
    normalized_dept = department if department in DEFAULT_DEPARTMENT else "default"
    normalized_doc_type = document_type if document_type in DOCUMENT_TYPES else DOCUMENT_TYPES[0]
    return normalized_dept, normalized_doc_type


def _check_model_switching(selected_model: str, total_characters: int) -> Tuple[str, bool, str]:
    """モデル切り替えの必要性をチェック"""
    original_model = selected_model
    model_switched = False

    if selected_model == "Claude" and total_characters > MAX_TOKEN_THRESHOLD:
        if GEMINI_CREDENTIALS and GEMINI_MODEL:
            selected_model = "Gemini_Pro"
            model_switched = True
        else:
            raise APIError(MESSAGES["TOKEN_THRESHOLD_EXCEEDED_NO_GEMINI"])

    return selected_model, model_switched, original_model


def _determine_final_model(department: str, document_type: str, doctor: str, 
                          selected_model: str, model_explicitly_selected: bool,
                          input_text: str, additional_info: str) -> Tuple[str, bool, str]:
    """最終的に使用するモデルを決定"""
    prompt_data = get_prompt(department, document_type, doctor)
    prompt_selected_model = prompt_data.get("selected_model") if prompt_data else None

    if prompt_selected_model and not model_explicitly_selected:
        selected_model = prompt_selected_model

    total_characters = len(input_text) + len(additional_info or "")
    return _check_model_switching(selected_model, total_characters)


def _get_provider_and_model(selected_model: str) -> Tuple[str, str]:
    """選択されたモデルからプロバイダーとモデル名を取得"""
    provider_mapping = {
        "Claude": ("claude", CLAUDE_MODEL),
        "Gemini_Pro": ("gemini", GEMINI_MODEL),
        "Gemini_Flash": ("gemini", GEMINI_FLASH_MODEL),
    }

    if selected_model not in provider_mapping:
        raise APIError(MESSAGES["NO_API_CREDENTIALS"])

    return provider_mapping[selected_model]


def _validate_provider_credentials(provider: str) -> None:
    """プロバイダー別の認証情報をチェック"""
    credentials_check = {
        "claude": CLAUDE_API_KEY,
        "gemini": GEMINI_CREDENTIALS,
    }

    if not credentials_check.get(provider):
        raise APIError(MESSAGES["NO_API_CREDENTIALS"])


def _display_progress_with_timer(thread: threading.Thread,
                                placeholder: st.empty,
                                start_time: datetime.datetime) -> None:
    """進捗表示とタイマー"""
    elapsed_time = 0
    with st.spinner("作成中..."):
        placeholder.text(f"⏱️ 経過時間: {elapsed_time}秒")
        while thread.is_alive():
            time.sleep(SystemConstants.PROGRESS_UPDATE_INTERVAL)
            elapsed_time = int((datetime.datetime.now() - start_time).total_seconds())
            placeholder.text(f"⏱️ 経過時間: {elapsed_time}秒")


def _save_usage_to_database(result: Dict[str, Any], session_params: Dict[str, Any]) -> None:
    """使用統計をデータベースに保存"""
    try:
        db_manager = DatabaseManager.get_instance()
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

        query = """
                INSERT INTO summary_usage
                (date, app_type, document_types, model_detail, department, doctor,
                 input_tokens, output_tokens, total_tokens, processing_time)
                VALUES (:date, :app_type, :document_types, :model_detail, :department, :doctor,
                        :input_tokens, :output_tokens, :total_tokens, :processing_time)
                """

        db_manager.execute_query(query, usage_data, fetch=False)

    except Exception as db_error:
        st.warning(f"データベース保存中にエラーが発生しました: {str(db_error)}")


def _handle_success_result(result: Dict[str, Any], session_params: Dict[str, Any]) -> None:
    """成功結果の処理"""
    st.session_state.output_summary = result["output_summary"]
    st.session_state.parsed_summary = result["parsed_summary"]

    if result.get("model_switched"):
        st.info(f"⚠️ 入力テキストが長いため{result['original_model']} からGemini_Proに切り替えました")

    _save_usage_to_database(result, session_params)


def generate_summary_task(input_text: str,
                          selected_department: str,
                          selected_model: str,
                          result_queue: queue.Queue,
                          additional_info: str = "",
                          current_prescription: str = "",
                          selected_document_type: str = DEFAULT_DOCUMENT_TYPE,
                          selected_doctor: str = "default",
                          model_explicitly_selected: bool = False) -> None:
    """サマリー生成タスクのメイン処理"""
    try:
        normalized_dept, normalized_doc_type = _normalize_parameters(
            selected_department, selected_document_type
        )

        final_model, model_switched, original_model = _determine_final_model(
            normalized_dept, normalized_doc_type, selected_doctor,
            selected_model, model_explicitly_selected, input_text, additional_info
        )

        provider, model_name = _get_provider_and_model(final_model)
        _validate_provider_credentials(provider)

        output_summary, input_tokens, output_tokens = generate_summary(
            provider=provider,
            medical_text=input_text,
            additional_info=additional_info,
            current_prescription=current_prescription,
            department=normalized_dept,
            document_type=normalized_doc_type,
            doctor=selected_doctor,
            model_name=model_name
        )

        model_detail = model_name if provider == "gemini" else final_model
        output_summary = format_output_summary(output_summary)
        parsed_summary = parse_output_summary(output_summary)

        result_queue.put({
            "success": True,
            "output_summary": output_summary,
            "parsed_summary": parsed_summary,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "model_detail": model_detail,
            "model_switched": model_switched,
            "original_model": original_model if model_switched else None
        })

    except Exception as e:
        result_queue.put({
            "success": False,
            "error": str(e)
        })


def _execute_summary_generation(input_text: str,
                               additional_info: str,
                               current_prescription: str,
                               session_params: Dict[str, Any]) -> Dict[str, Any]:
    """サマリー生成の実行とUI制御"""
    start_time = datetime.datetime.now()
    status_placeholder = st.empty()
    result_queue = queue.Queue()

    summary_thread = threading.Thread(
        target=generate_summary_task,
        args=(
            input_text,
            session_params["selected_department"],
            session_params["selected_model"],
            result_queue,
            additional_info,
            current_prescription,
            session_params["selected_document_type"],
            session_params["selected_doctor"],
            session_params["model_explicitly_selected"]
        ),
    )
    summary_thread.start()

    _display_progress_with_timer(summary_thread, status_placeholder, start_time)

    summary_thread.join()
    status_placeholder.empty()
    result = result_queue.get()

    if result["success"]:
        processing_time = (datetime.datetime.now() - start_time).total_seconds()
        st.session_state.summary_generation_time = processing_time
        result["processing_time"] = processing_time

    return result


@handle_error
def process_summary(input_text: str,
                    additional_info: str = "",
                    current_prescription: str = "") -> None:
    """サマリー処理のエントリーポイント"""
    _validate_api_credentials()
    _validate_inputs(input_text)

    try:
        session_params = _get_session_parameters()
        result = _execute_summary_generation(
            input_text, additional_info, current_prescription, session_params
        )

        if result["success"]:
            _handle_success_result(result, session_params)
        else:
            raise APIError(result['error'])

    except Exception as e:
        raise APIError(f"作成中にエラーが発生しました: {str(e)}")


# 後方互換性のために残す非推奨関数群
def validate_api_credentials():
    return _validate_api_credentials()

def validate_input_text(input_text: str):
    return _validate_inputs(input_text)

def get_session_parameters():
    return _get_session_parameters()

def normalize_selection_params(department: str, document_type: str):
    return _normalize_parameters(department, document_type)

def determine_final_model(department: str, document_type: str, doctor: str,
                         selected_model: str, model_explicitly_selected: bool,
                         input_text: str, additional_info: str):
    return _determine_final_model(department, document_type, doctor,
                                 selected_model, model_explicitly_selected,
                                 input_text, additional_info)

def get_provider_and_model(selected_model: str):
    return _get_provider_and_model(selected_model)

def validate_api_credentials_for_provider(provider: str):
    return _validate_provider_credentials(provider)

def execute_summary_generation_with_ui(input_text: str, additional_info: str,
                                      current_prescription: str, session_params: Dict[str, Any]):
    return _execute_summary_generation(input_text, additional_info,
                                      current_prescription, session_params)

def display_progress_with_timer(thread: threading.Thread, placeholder: st.empty,
                               start_time: datetime.datetime):
    return _display_progress_with_timer(thread, placeholder, start_time)

def handle_success_result(result: Dict[str, Any], session_params: Dict[str, Any]):
    return _handle_success_result(result, session_params)

def save_usage_to_database(result: Dict[str, Any], session_params: Dict[str, Any]):
    return _save_usage_to_database(result, session_params)