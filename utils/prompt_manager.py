import datetime
from typing import Dict, Any, Optional, Tuple

from database.db import DatabaseManager
from utils.config import get_config
from utils.constants import DEFAULT_DEPARTMENT, DOCUMENT_TYPES, DEPARTMENT_DOCTORS_MAPPING, DEFAULT_DOCUMENT_TYPE
from utils.exceptions import DatabaseError, AppError
from database.schema import initialize_database as init_schema


class PromptManager:

    def __init__(self):
        self.db_manager = DatabaseManager.get_instance()
        self.default_prompt_content = get_config()['PROMPTS']['summary']

    def get_prompt(self, department: str = "default",
                   document_type: str = DEFAULT_DOCUMENT_TYPE,
                   doctor: str = "default") -> Optional[Dict[str, Any]]:
        try:
            conditions = {
                "department": department,
                "document_type": document_type,
                "doctor": doctor
            }

            prompts = self.db_manager.select_with_conditions("prompts", conditions)

            if prompts:
                return prompts[0]

            default_conditions = {
                "department": "default",
                "document_type": DEFAULT_DOCUMENT_TYPE,
                "doctor": "default",
                "is_default": True
            }

            default_prompts = self.db_manager.select_with_conditions("prompts", default_conditions)
            return default_prompts[0] if default_prompts else None

        except Exception as e:
            raise DatabaseError(f"プロンプトの取得に失敗しました: {str(e)}")

    def create_or_update_prompt(self, department: str, document_type: str,
                                doctor: str, content: str,
                                selected_model: Optional[str] = None) -> Tuple[bool, str]:
        try:
            if not all([department, document_type, doctor, content]):
                return False, "すべての項目を入力してください"

            existing_prompt = self.get_prompt(department, document_type, doctor)
            is_exact_match = (existing_prompt and
                              existing_prompt.get("department") == department and
                              existing_prompt.get("document_type") == document_type and
                              existing_prompt.get("doctor") == doctor)

            prompt_data = {
                "department": department,
                "document_type": document_type,
                "doctor": doctor,
                "content": content,
                "selected_model": selected_model,
                "is_default": False,
                "updated_at": datetime.datetime.now()
            }

            if not is_exact_match:
                prompt_data["created_at"] = datetime.datetime.now()

            conflict_columns = ["department", "document_type", "doctor"]
            self.db_manager.upsert_record("prompts", prompt_data, conflict_columns)

            action = "更新" if is_exact_match else "新規作成"
            return True, f"プロンプトを{action}しました"

        except DatabaseError as e:
            return False, str(e)
        except Exception as e:
            raise AppError(f"プロンプトの作成/更新中にエラーが発生しました: {str(e)}")

    def delete_prompt(self, department: str, document_type: str,
                      doctor: str) -> Tuple[bool, str]:
        try:
            if (department == "default" and
                    document_type == DEFAULT_DOCUMENT_TYPE and
                    doctor == "default"):
                return False, "デフォルトプロンプトは削除できません"

            conditions = {
                "department": department,
                "document_type": document_type,
                "doctor": doctor
            }

            deleted_count = self.db_manager.delete_with_conditions("prompts", conditions)

            if deleted_count == 0:
                return False, "プロンプトが見つかりません"

            return True, "プロンプトを削除しました"

        except DatabaseError as e:
            return False, str(e)
        except Exception as e:
            raise AppError(f"プロンプトの削除中にエラーが発生しました: {str(e)}")

    def get_all_prompts(self) -> list:
        try:
            return self.db_manager.select_with_conditions(
                "prompts",
                order_by=["department", "document_type", "doctor"]
            )
        except Exception as e:
            raise DatabaseError(f"プロンプト一覧の取得に失敗しました: {str(e)}")

    def initialize_default_prompt(self):
        try:
            default_conditions = {
                "department": "default",
                "document_type": DEFAULT_DOCUMENT_TYPE,
                "doctor": "default",
                "is_default": True
            }

            existing_default = self.db_manager.select_with_conditions("prompts", default_conditions)

            if not existing_default:
                default_data = {
                    "department": "default",
                    "document_type": DEFAULT_DOCUMENT_TYPE,
                    "doctor": "default",
                    "content": self.default_prompt_content,
                    "is_default": True,
                    "created_at": datetime.datetime.now(),
                    "updated_at": datetime.datetime.now()
                }

                conflict_columns = ["department", "document_type", "doctor"]
                self.db_manager.upsert_record("prompts", default_data, conflict_columns)

        except Exception as e:
            raise DatabaseError(f"デフォルトプロンプトの初期化に失敗しました: {str(e)}")

    def initialize_all_prompts(self):
        try:
            for dept in DEFAULT_DEPARTMENT:
                doctors = DEPARTMENT_DOCTORS_MAPPING.get(dept, ["default"])
                for doctor in doctors:
                    for doc_type in DOCUMENT_TYPES:
                        existing = self.get_prompt(dept, doc_type, doctor)
                        is_exact_match = (existing and
                                          existing.get("department") == dept and
                                          existing.get("document_type") == doc_type and
                                          existing.get("doctor") == doctor)

                        if not is_exact_match:
                            prompt_data = {
                                "department": dept,
                                "document_type": doc_type,
                                "doctor": doctor,
                                "content": self.default_prompt_content,
                                "is_default": False,
                                "created_at": datetime.datetime.now(),
                                "updated_at": datetime.datetime.now()
                            }

                            conflict_columns = ["department", "document_type", "doctor"]
                            self.db_manager.upsert_record("prompts", prompt_data, conflict_columns)

        except Exception as e:
            raise DatabaseError(f"プロンプト初期化に失敗しました: {str(e)}")


_prompt_manager = None


def get_prompt_manager() -> PromptManager:
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager


def initialize_database():
    """データベースの初期化（スキーマ作成とプロンプト初期化）"""
    try:
        init_schema()
        prompt_manager = get_prompt_manager()
        prompt_manager.initialize_default_prompt()
        prompt_manager.initialize_all_prompts()
    except Exception as e:
        raise DatabaseError(f"データベースの初期化に失敗しました: {str(e)}")

