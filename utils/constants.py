import os

from utils.config import APP_TYPE

DEFAULT_DEPARTMENT = ["default","内科", "消化器内科", "整形外科"]
DEFAULT_DOCTOR = ["default"]

DEPARTMENT_DOCTORS_MAPPING = {
    "default": ["default","医師共通"],
}

DEFAULT_DOCUMENT_TYPE = "退院時サマリ"
DOCUMENT_TYPES = ["退院時サマリ", "現病歴"]
DOCUMENT_NAME_OPTIONS = ["退院時サマリ", "現病歴", "すべて"]

MODEL_OPTIONS =  ["すべて", "Claude", "Gemini_Pro", "Gemini_Flash"]

DEFAULT_SECTION_NAMES = [
    "入院期間", "現病歴", "入院時検査", "入院中の治療経過", "退院申し送り", "備考"
]

TAB_NAMES = {
    "ALL": "全文",
    "ADMISSION_PERIOD": "【入院期間】",
    "CURRENT_ILLNESS": "【現病歴】",
    "ADMISSION_TESTS": "【入院時検査】",
    "TREATMENT_PROGRESS": "【入院中の治療経過】",
    "DISCHARGE_NOTES": "【退院申し送り】",
    "NOTE": "【備考】"
}

MESSAGES = {
    "PROMPT_UPDATED": "プロンプトを更新しました",
    "PROMPT_CREATED": "プロンプトを新規作成しました",
    "PROMPT_DELETED": "プロンプトを削除しました",

    "NO_DATA_FOUND": "指定期間のデータがありません",

    "FIELD_REQUIRED": "すべての項目を入力してください",
    "NO_INPUT": "⚠️ カルテ情報を入力してください",
    "INPUT_TOO_SHORT": "⚠️ 入力テキストが短すぎます",
    "INPUT_TOO_LONG": "⚠️ 入力テキストが長すぎます",
    "TOKEN_THRESHOLD_EXCEEDED": "⚠️ 入力テキストが長いため{original_model} から Gemini_Pro に切り替えます",
    "TOKEN_THRESHOLD_EXCEEDED_NO_GEMINI": "⚠️ Gemini APIの認証情報が設定されていないため処理できません。",
    "API_CREDENTIALS_MISSING": "⚠️ Gemini APIの認証情報が設定されていません。環境変数を確認してください。",
    "NO_API_CREDENTIALS": "⚠️ 使用可能なAI APIの認証情報が設定されていません。環境変数を確認してください。",
    "VERTEX_AI_PROJECT_MISSING": "⚠️ GOOGLE_PROJECT_ID環境変数が設定されていません。",
    "VERTEX_AI_LOCATION_MISSING": "⚠️ GOOGLE_LOCATION環境変数が設定されていません。",
    "VERTEX_AI_CREDENTIALS_MISSING": "⚠️ Vertex AI APIの認証情報が設定されていません。環境変数を確認してください。",
    "VERTEX_AI_INIT_ERROR": "Vertex AI Gemini API初期化エラー: {error}",
    "COPY_INSTRUCTION": "💡 テキストエリアの右上にマウスを合わせて左クリックでコピーできます",
    "PROCESSING_TIME": "⏱️ 処理時間: {processing_time:.0f}秒",
}
