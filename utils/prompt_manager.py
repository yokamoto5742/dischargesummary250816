import datetime
from typing import Dict, Any, Optional, Tuple, List

from database.db import get_prompt_repository
from database.repositories import PromptRepository
from utils.config import get_config
from utils.constants import DEFAULT_DEPARTMENT, DOCUMENT_TYPES, DEPARTMENT_DOCTORS_MAPPING, DEFAULT_DOCUMENT_TYPE
from utils.exceptions import DatabaseError, AppError


class PromptManager:

    def __init__(self):
        self.prompt_repository: PromptRepository = get_prompt_repository()
        self.default_prompt_content = get_config()['PROMPTS']['summary']

    def get_prompt(self, department: str = "default",
                   document_type: str = DEFAULT_DOCUMENT_TYPE,
                   doctor: str = "default") -> Optional[Dict[str, Any]]:
        try:
            prompt = self.prompt_repository.get_by_keys(department, document_type, doctor)

            if prompt:
                return {
                    'id': prompt.id,
                    'department': prompt.department,
                    'document_type': prompt.document_type,
                    'doctor': prompt.doctor,
                    'content': prompt.content,
                    'selected_model': prompt.selected_model,
                    'is_default': prompt.is_default,
                    'created_at': prompt.created_at,
                    'updated_at': prompt.updated_at
                }

            default_prompt = self.prompt_repository.get_default_prompt()
            if default_prompt:
                return {
                    'id': default_prompt.id,
                    'department': default_prompt.department,
                    'document_type': default_prompt.document_type,
                    'doctor': default_prompt.doctor,
                    'content': default_prompt.content,
                    'selected_model': default_prompt.selected_model,
                    'is_default': default_prompt.is_default,
                    'created_at': default_prompt.created_at,
                    'updated_at': default_prompt.updated_at
                }

            return None

        except DatabaseError as e:
            raise e
        except Exception as e:
            raise DatabaseError(f"プロンプトの取得に失敗しました: {str(e)}")

    def create_or_update_prompt(self, department: str, document_type: str,
                                doctor: str, content: str,
                                selected_model: Optional[str] = None) -> Tuple[bool, str]:
        try:
            if not all([department, document_type, doctor, content]):
                return False, "すべての項目を入力してください"

            return self.prompt_repository.create_or_update(
                department, document_type, doctor, content, selected_model
            )

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

            return self.prompt_repository.delete_by_keys(department, document_type, doctor)

        except DatabaseError as e:
            return False, str(e)
        except Exception as e:
            raise AppError(f"プロンプトの削除中にエラーが発生しました: {str(e)}")

    def get_all_prompts(self) -> List[Dict[str, Any]]:
        try:
            prompts = self.prompt_repository.get_all()
            return [
                {
                    'id': p.id,
                    'department': p.department,
                    'document_type': p.document_type,
                    'doctor': p.doctor,
                    'content': p.content,
                    'selected_model': p.selected_model,
                    'is_default': p.is_default,
                    'created_at': p.created_at,
                    'updated_at': p.updated_at
                }
                for p in prompts
            ]
        except Exception as e:
            raise DatabaseError(f"プロンプト一覧の取得に失敗しました: {str(e)}")

    def initialize_default_prompt(self):
        try:
            self.prompt_repository.create_default_prompt(self.default_prompt_content)
        except Exception as e:
            raise DatabaseError(f"デフォルトプロンプトの初期化に失敗しました: {str(e)}")

    def initialize_all_prompts(self):
        try:
            prompts_data = []

            for dept in DEFAULT_DEPARTMENT:
                doctors = DEPARTMENT_DOCTORS_MAPPING.get(dept, ["default"])
                for doctor in doctors:
                    for doc_type in DOCUMENT_TYPES:
                        prompts_data.append({
                            'department': dept,
                            'document_type': doc_type,
                            'doctor': doctor,
                            'content': self.default_prompt_content,
                            'is_default': False,
                            'created_at': datetime.datetime.now(),
                            'updated_at': datetime.datetime.now()
                        })

            self.prompt_repository.bulk_create_prompts(prompts_data)

        except Exception as e:
            raise DatabaseError(f"プロンプト初期化に失敗しました: {str(e)}")


_prompt_manager = None


def get_prompt_manager() -> PromptManager:
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
