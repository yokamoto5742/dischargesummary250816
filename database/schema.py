import time

from sqlalchemy import text

from database.db import DatabaseManager
from utils.exceptions import DatabaseError


def create_tables():
    db_manager = DatabaseManager.get_instance()
    engine = db_manager.get_engine()

    app_settings_table = """
        CREATE TABLE IF NOT EXISTS app_settings (
            id SERIAL PRIMARY KEY,
            setting_id VARCHAR(100) NOT NULL,
            app_type VARCHAR(50) NOT NULL,
            selected_department VARCHAR(100),
            selected_model VARCHAR(50),
            selected_document_type VARCHAR(100),
            selected_doctor VARCHAR(100),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_setting_per_app UNIQUE (setting_id, app_type)
        )
    """

    prompts_table = """
        CREATE TABLE IF NOT EXISTS prompts (
            id SERIAL PRIMARY KEY,
            department VARCHAR(100) NOT NULL,
            document_type VARCHAR(100) NOT NULL,
            doctor VARCHAR(100) NOT NULL,
            content TEXT NOT NULL,
            selected_model VARCHAR(50),
            is_default BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_prompt UNIQUE (department, document_type, doctor)
        )
    """

    summary_usage_table = """
        CREATE TABLE IF NOT EXISTS summary_usage (
            id SERIAL PRIMARY KEY,
            date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            app_type VARCHAR(50),
            document_types VARCHAR(100),
            model_detail VARCHAR(100),
            department VARCHAR(100),
            doctor VARCHAR(100),
            input_tokens INTEGER,
            output_tokens INTEGER,
            total_tokens INTEGER,
            processing_time INTEGER
        )
    """

    try:
        with engine.begin() as conn:
            conn.execute(text(app_settings_table))
            conn.execute(text(prompts_table))
            conn.execute(text(summary_usage_table))
        return True
    except Exception as e:
        raise DatabaseError(f"テーブル作成中にエラーが発生しました: {str(e)}")


def initialize_database():
    max_retries = 5
    retry_count = 0
    last_error = None

    while retry_count < max_retries:
        try:
            create_tables()
            return True
        except Exception as e:
            last_error = e
            retry_count += 1
            wait_time = 2 ** retry_count  # 指数バックオフ
            print(f"データベース初期化に失敗しました（試行 {retry_count}/{max_retries}）: {str(e)}")
            print(f"{wait_time}秒後に再試行します...")
            time.sleep(wait_time)

    raise DatabaseError(f"データベースの初期化に失敗しました: {str(last_error)}")
