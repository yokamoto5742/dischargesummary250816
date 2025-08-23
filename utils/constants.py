import os

from utils.config import APP_TYPE

# 既存の定数
DEFAULT_DEPARTMENT = ["default","内科", "消化器内科", "整形外科"]
DEFAULT_DOCTOR = ["default"]

DEPARTMENT_DOCTORS_MAPPING = {
    "default": ["default","医師共通"],
}

DEFAULT_DOCUMENT_TYPE = "退院時サマリ"
DOCUMENT_TYPES = ["退院時サマリ", "現病歴"]
DOCUMENT_NAME_OPTIONS = ["退院時サマリ", "現病歴", "すべて"]

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

# UI関連の定数
class UIConstants:
    # テキストエリアの高さ
    TEXT_AREA_HEIGHT_SMALL = 70
    TEXT_AREA_HEIGHT_MEDIUM = 150
    TEXT_AREA_HEIGHT_LARGE = 200
    
    # コードブロックの高さ
    CODE_BLOCK_HEIGHT_SMALL = 150
    
    # カラム設定
    COLUMNS_TWO = 2
    COLUMNS_FOUR = 4

# システム関連の定数
class SystemConstants:
    # データベース関連
    DB_MAX_RETRIES = 5
    DB_RETRY_BASE_WAIT = 2
    
    # API関連
    CLAUDE_MAX_TOKENS = 6000
    
    # 処理時間関連
    PROGRESS_UPDATE_INTERVAL = 1  # 秒
    
    # セッション管理
    DEFAULT_TIMEOUT = 30  # 秒

# 統計関連の定数
class StatisticsConstants:
    DEFAULT_DAYS_BACK = 7
    MODEL_OPTIONS = ["すべて", "Claude", "Gemini_Pro", "Gemini_Flash"]
    
    MODEL_MAPPING = {
        "Gemini_Pro": {"pattern": "gemini", "exclude": "flash"},
        "Gemini_Flash": {"pattern": "flash", "exclude": None},
        "Claude": {"pattern": "claude", "exclude": None},
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
    "CLAUDE_API_CREDENTIALS_MISSING": "⚠️ Claude APIの認証情報が設定されていません。環境変数を確認してください。",
    "NO_API_CREDENTIALS": "⚠️ 使用可能なAI APIの認証情報が設定されていません。環境変数を確認してください。",
    "COPY_INSTRUCTION": "💡 テキストエリアの右上にマウスを合わせて左クリックでコピーできます",
    "PROCESSING_TIME": "⏱️ 処理時間: {processing_time:.0f}秒",
}