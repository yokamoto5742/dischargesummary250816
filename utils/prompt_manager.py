import datetime

from sqlalchemy import text

from database.db import DatabaseManager
from utils.config import get_config
from utils.constants import DEFAULT_DEPARTMENT, DOCUMENT_TYPES, DEPARTMENT_DOCTORS_MAPPING, DEFAULT_DOCUMENT_TYPE
from utils.exceptions import DatabaseError, AppError
from database.schema import initialize_database as init_schema


def get_prompt_collection():
    try:
        db_manager = DatabaseManager.get_instance()
        return db_manager
    except Exception as e:
        raise DatabaseError(f"プロンプトコレクションの取得に失敗しました: {str(e)}")


def get_current_datetime():
    return datetime.datetime.now()


def update_document(collection, query_dict, update_data):
    try:
        now = get_current_datetime()
        update_data.update({"updated_at": now})

        if "department" in query_dict:
            query = """
                    UPDATE prompts
                    SET name       = :name,
                        content    = :content,
                        updated_at = :updated_at
                    WHERE department = :department
                    """
            params = {
                "name": update_data.get("name"),
                "content": update_data.get("content"),
                "updated_at": update_data["updated_at"],
                "department": query_dict["department"]
            }
        elif "name" in query_dict:
            set_clauses = []
            params = {"name": query_dict["name"], "updated_at": update_data["updated_at"]}

            if "default_model" in update_data:
                set_clauses.append("default_model = :default_model")
                params["default_model"] = update_data["default_model"]

            if "order_index" in update_data:
                set_clauses.append("order_index = :order_index")
                params["order_index"] = update_data["order_index"]

            query = f"""
            UPDATE departments
            SET {', '.join(set_clauses)}, updated_at = :updated_at
            WHERE name = :name
            """
        else:
            raise ValueError("不明な更新条件です")

        collection.execute_query(query, params, fetch=False)
        return True

    except Exception as e:
        raise DatabaseError(f"ドキュメントの更新に失敗しました: {str(e)}")


def get_all_departments():
    return DEFAULT_DEPARTMENT


def get_all_prompts():
    try:
        prompt_collection = get_prompt_collection()
        query = "SELECT * FROM prompts ORDER BY department"
        return prompt_collection.execute_query(query)
    except Exception as e:
        raise DatabaseError(f"プロンプト一覧の取得に失敗しました: {str(e)}")


def create_or_update_prompt(department,
                            document_type,
                            doctor, content,
                            selected_model=None):
    try:
        if not department or not document_type or not doctor or not content:
            return False, "すべての項目を入力してください"

        prompt_collection = get_prompt_collection()

        query = "SELECT * FROM prompts WHERE department = :department AND document_type = :document_type AND doctor = :doctor"
        existing = prompt_collection.execute_query(query, {
            "department": department,
            "document_type": document_type,
            "doctor": doctor
        })

        if existing:
            update_query = """
                           UPDATE prompts
                           SET content       = :content,
                               selected_model = :selected_model,
                               updated_at = CURRENT_TIMESTAMP
                           WHERE department = :department AND document_type = :document_type AND doctor = :doctor
                           """

            prompt_collection.execute_query(update_query, {
                "department": department,
                "document_type": document_type,
                "doctor": doctor,
                "content": content,
                "selected_model": selected_model
            }, fetch=False)
            return True, "プロンプトを更新しました"
        else:
            insert_document(prompt_collection, {
                "department": department,
                "document_type": document_type,
                "doctor": doctor,
                "content": content,
                "selected_model": selected_model,
                "is_default": False
            })
            return True, "プロンプトを新規作成しました"
    except DatabaseError as e:
        return False, str(e)
    except Exception as e:
        raise AppError(f"プロンプトの作成/更新中にエラーが発生しました: {str(e)}")


def delete_prompt(department, document_type, doctor):
    try:
        if department == "default" and document_type == DEFAULT_DOCUMENT_TYPE and doctor == "default":
            return False, "デフォルトプロンプトは削除できません"

        prompt_collection = get_prompt_collection()

        session = prompt_collection.get_session()
        try:
            prompt_query = "DELETE FROM prompts WHERE department = :department AND document_type = :document_type AND doctor = :doctor"
            result = session.execute(text(prompt_query), {
                "department": department,
                "document_type": document_type,
                "doctor": doctor
            })
            deleted_count = result.rowcount

            if deleted_count == 0:
                session.rollback()
                return False, "プロンプトが見つかりません"

            session.commit()
            return True, "プロンプトを削除しました"
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    except DatabaseError as e:
        return False, str(e)
    except Exception as e:
        raise AppError(f"プロンプトの削除中にエラーが発生しました: {str(e)}")


def insert_document(collection, document):
    try:
        now = get_current_datetime()
        document.update({
            "created_at": now,
            "updated_at": now
        })

        if "name" in document and "order_index" in document:
            query = """
                    INSERT INTO departments (name, order_index, default_model, created_at, updated_at)
                    VALUES (:name, :order_index, :default_model, :created_at, :updated_at) RETURNING id; \
                    """
            params = {
                "name": document["name"],
                "order_index": document["order_index"],
                "default_model": document.get("default_model"),
                "created_at": document["created_at"],
                "updated_at": document["updated_at"]
            }
        elif "department" in document:
            query = """
                    INSERT INTO prompts (department, document_type, doctor, content, selected_model, is_default, created_at, updated_at)
                    VALUES (:department, :document_type, :doctor, :content, :selected_model, :is_default, :created_at, :updated_at) RETURNING id; \
                    """
            params = {
                "department": document["department"],
                "document_type": document.get("document_type"),
                "doctor": document["doctor"],
                "content": document["content"],
                "selected_model": document.get("selected_model"),
                "is_default": document.get("is_default", False),
                "created_at": document["created_at"],
                "updated_at": document["updated_at"]
            }
        else:
            raise ValueError("不明なドキュメント形式です")

        result = collection.execute_query(query, params)
        return result[0]["id"] if result else None

    except Exception as e:
        raise DatabaseError(f"ドキュメントの挿入に失敗しました: {str(e)}")


def initialize_default_prompt():
    try:
        prompt_collection = get_prompt_collection()

        query = f"SELECT * FROM prompts WHERE department = 'default' AND document_type = '{DEFAULT_DOCUMENT_TYPE}' AND doctor = 'default' AND is_default = true"
        default_prompt = prompt_collection.execute_query(query)

        if not default_prompt:
            config = get_config()
            default_prompt_content = config['PROMPTS']['summary']

            insert_document(prompt_collection, {
                "department": "default",
                "document_type": DEFAULT_DOCUMENT_TYPE,
                "doctor": "default",
                "content": default_prompt_content,
                "is_default": True
            })
    except Exception as e:
        raise DatabaseError(f"デフォルトプロンプトの初期化に失敗しました: {str(e)}")


def get_prompt(department="default",
               document_type=DEFAULT_DOCUMENT_TYPE,
               doctor="default"):
    try:
        prompt_collection = get_prompt_collection()
        query = "SELECT * FROM prompts WHERE department = :department AND document_type = :document_type AND doctor = :doctor"
        prompt = prompt_collection.execute_query(query, {
            "department": department,
            "document_type": document_type,
            "doctor": doctor
        })

        if not prompt:
            default_query = f"SELECT * FROM prompts WHERE department = 'default' AND document_type = '{DEFAULT_DOCUMENT_TYPE}' AND doctor = 'default' AND is_default = true"
            prompt = prompt_collection.execute_query(default_query)

        return prompt[0] if prompt else None
    except Exception as e:
        raise DatabaseError(f"プロンプトの取得に失敗しました: {str(e)}")


def initialize_database():
    try:
        init_schema()
        initialize_default_prompt()

        prompt_collection = get_prompt_collection()
        config = get_config()
        default_prompt_content = config['PROMPTS']['summary']
        departments = DEFAULT_DEPARTMENT
        document_types = DOCUMENT_TYPES

        for dept in departments:
            doctors = DEPARTMENT_DOCTORS_MAPPING.get(dept, ["default"])
            for doctor in doctors:
                for doc_type in document_types:
                    check_query = """
                                  SELECT *
                                  FROM prompts
                                  WHERE department = :department
                                    AND document_type = :document_type
                                    AND doctor = :doctor
                                  """

                    existing = prompt_collection.execute_query(check_query, {
                        "department": dept,
                        "document_type": doc_type,
                        "doctor": doctor
                    })

                    if not existing:
                        insert_document(prompt_collection, {
                            "department": dept,
                            "document_type": doc_type,
                            "doctor": doctor,
                            "content": default_prompt_content,
                            "is_default": False
                        })

    except Exception as e:
        raise DatabaseError(f"データベースの初期化に失敗しました: {str(e)}")
