import datetime
from typing import Dict, Any, List, Optional
import pytz

from database.db import DatabaseManager
from utils.constants import StatisticsConstants
from utils.exceptions import DatabaseError

JST = pytz.timezone('Asia/Tokyo')


class StatisticsQueries:
    """統計関連のデータベースクエリクラス"""
    
    def __init__(self):
        self.db_manager = DatabaseManager.get_instance()
    
    def _build_where_conditions(self, 
                               start_date: datetime.datetime,
                               end_date: datetime.datetime,
                               selected_model: str = "すべて",
                               selected_document_type: str = "すべて") -> tuple:
        """WHERE条件とパラメータを構築"""
        conditions = []
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        conditions.append("date >= :start_date AND date <= :end_date")
        
        # モデルフィルター
        if selected_model != "すべて":
            model_config = StatisticsConstants.MODEL_MAPPING.get(selected_model)
            if model_config:
                conditions.append("model_detail ILIKE :model_pattern")
                params["model_pattern"] = f"%{model_config['pattern']}%"
                
                if model_config["exclude"]:
                    conditions.append("model_detail NOT ILIKE :model_exclude")
                    params["model_exclude"] = f"%{model_config['exclude']}%"
        
        # 文書タイプフィルター
        if selected_document_type != "すべて":
            if selected_document_type == "不明":
                conditions.append("document_types IS NULL")
            else:
                conditions.append("document_types = :doc_type")
                params["doc_type"] = selected_document_type
        
        where_clause = " AND ".join(conditions)
        return where_clause, params
    
    def get_total_summary(self,
                         start_date: datetime.datetime,
                         end_date: datetime.datetime,
                         selected_model: str = "すべて",
                         selected_document_type: str = "すべて") -> Optional[Dict[str, Any]]:
        """期間内の総計データを取得"""
        try:
            where_clause, params = self._build_where_conditions(
                start_date, end_date, selected_model, selected_document_type
            )
            
            query = f"""
            SELECT
                COUNT(*) as count,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens,
                SUM(total_tokens) as total_tokens
            FROM summary_usage
            WHERE {where_clause}
            """
            
            result = self.db_manager.execute_query(query, params)
            return result[0] if result else None
            
        except Exception as e:
            raise DatabaseError(f"総計データの取得に失敗しました: {str(e)}")
    
    def get_department_summary(self,
                              start_date: datetime.datetime,
                              end_date: datetime.datetime,
                              selected_model: str = "すべて",
                              selected_document_type: str = "すべて") -> List[Dict[str, Any]]:
        """部門別集計データを取得"""
        try:
            where_clause, params = self._build_where_conditions(
                start_date, end_date, selected_model, selected_document_type
            )
            
            query = f"""
            SELECT
                COALESCE(department, 'default') as department,
                COALESCE(doctor, 'default') as doctor,
                document_types,
                COUNT(*) as count,
                SUM(input_tokens) as input_tokens,
                SUM(output_tokens) as output_tokens,
                SUM(total_tokens) as total_tokens,
                SUM(processing_time) as processing_time
            FROM summary_usage
            WHERE {where_clause}
            GROUP BY department, doctor, document_types
            ORDER BY count DESC
            """
            
            return self.db_manager.execute_query(query, params)
            
        except Exception as e:
            raise DatabaseError(f"部門別集計データの取得に失敗しました: {str(e)}")
    
    def get_detailed_records(self,
                            start_date: datetime.datetime,
                            end_date: datetime.datetime,
                            selected_model: str = "すべて",
                            selected_document_type: str = "すべて") -> List[Dict[str, Any]]:
        """詳細レコードを取得"""
        try:
            where_clause, params = self._build_where_conditions(
                start_date, end_date, selected_model, selected_document_type
            )
            
            query = f"""
            SELECT
                date,
                document_types,
                model_detail,
                department,
                doctor,
                input_tokens,
                output_tokens,
                processing_time
            FROM summary_usage
            WHERE {where_clause}
            ORDER BY date DESC
            """
            
            return self.db_manager.execute_query(query, params)
            
        except Exception as e:
            raise DatabaseError(f"詳細レコードの取得に失敗しました: {str(e)}")


class PromptQueries:
    """プロンプト関連のデータベースクエリクラス"""
    
    def __init__(self):
        self.db_manager = DatabaseManager.get_instance()
    
    def get_prompt_by_criteria(self, 
                              department: str = "default",
                              document_type: str = "退院時サマリ",
                              doctor: str = "default") -> Optional[Dict[str, Any]]:
        """条件によるプロンプト取得"""
        try:
            query = """
            SELECT * FROM prompts 
            WHERE department = :department 
            AND document_type = :document_type 
            AND doctor = :doctor
            """
            
            params = {
                "department": department,
                "document_type": document_type,
                "doctor": doctor
            }
            
            result = self.db_manager.execute_query(query, params)
            return result[0] if result else None
            
        except Exception as e:
            raise DatabaseError(f"プロンプトの取得に失敗しました: {str(e)}")
    
    def get_default_prompt(self) -> Optional[Dict[str, Any]]:
        """デフォルトプロンプトを取得"""
        try:
            query = """
            SELECT * FROM prompts 
            WHERE department = 'default' 
            AND document_type = '退院時サマリ' 
            AND doctor = 'default' 
            AND is_default = true
            """
            
            result = self.db_manager.execute_query(query)
            return result[0] if result else None
            
        except Exception as e:
            raise DatabaseError(f"デフォルトプロンプトの取得に失敗しました: {str(e)}")
    
    def create_or_update_prompt(self,
                               department: str,
                               document_type: str,
                               doctor: str,
                               content: str,
                               selected_model: Optional[str] = None) -> tuple:
        """プロンプトの作成または更新"""
        try:
            # 既存確認
            existing = self.get_prompt_by_criteria(department, document_type, doctor)
            
            if existing:
                # 更新
                query = """
                UPDATE prompts
                SET content = :content,
                    selected_model = :selected_model,
                    updated_at = CURRENT_TIMESTAMP
                WHERE department = :department 
                AND document_type = :document_type 
                AND doctor = :doctor
                """
                
                params = {
                    "department": department,
                    "document_type": document_type,
                    "doctor": doctor,
                    "content": content,
                    "selected_model": selected_model
                }
                
                self.db_manager.execute_query(query, params, fetch=False)
                return True, "プロンプトを更新しました"
            else:
                # 新規作成
                query = """
                INSERT INTO prompts 
                (department, document_type, doctor, content, selected_model, is_default, created_at, updated_at)
                VALUES (:department, :document_type, :doctor, :content, :selected_model, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                
                params = {
                    "department": department,
                    "document_type": document_type,
                    "doctor": doctor,
                    "content": content,
                    "selected_model": selected_model
                }
                
                self.db_manager.execute_query(query, params, fetch=False)
                return True, "プロンプトを新規作成しました"
                
        except Exception as e:
            return False, f"プロンプトの保存に失敗しました: {str(e)}"
    
    def delete_prompt(self,
                     department: str,
                     document_type: str,
                     doctor: str) -> tuple:
        """プロンプトの削除"""
        try:
            # デフォルトプロンプトは削除不可
            if (department == "default" and 
                document_type == "退院時サマリ" and 
                doctor == "default"):
                return False, "デフォルトプロンプトは削除できません"
            
            query = """
            DELETE FROM prompts 
            WHERE department = :department 
            AND document_type = :document_type 
            AND doctor = :doctor
            """
            
            params = {
                "department": department,
                "document_type": document_type,
                "doctor": doctor
            }
            
            session = self.db_manager.get_session()
            try:
                from sqlalchemy import text
                result = session.execute(text(query), params)
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
                
        except Exception as e:
            return False, f"プロンプトの削除に失敗しました: {str(e)}"


class SettingsQueries:
    """設定関連のデータベースクエリクラス"""
    
    def __init__(self):
        self.db_manager = DatabaseManager.get_instance()
    
    def save_user_settings(self,
                          setting_id: str,
                          app_type: str,
                          department: str,
                          model: str,
                          document_type: str = "退院時サマリ",
                          doctor: str = "default") -> bool:
        """ユーザー設定の保存"""
        try:
            query = """
            INSERT INTO app_settings
            (setting_id, app_type, selected_department, selected_model,
             selected_document_type, selected_doctor, updated_at)
            VALUES (:setting_id, :app_type, :department, :model,
                    :document_type, :doctor, CURRENT_TIMESTAMP) 
            ON CONFLICT (setting_id, app_type) 
            DO UPDATE SET
                selected_department = EXCLUDED.selected_department,
                selected_model = EXCLUDED.selected_model,
                selected_document_type = EXCLUDED.selected_document_type,
                selected_doctor = EXCLUDED.selected_doctor,
                updated_at = CURRENT_TIMESTAMP
            """
            
            params = {
                "setting_id": setting_id,
                "app_type": app_type,
                "department": department,
                "model": model,
                "document_type": document_type,
                "doctor": doctor
            }
            
            self.db_manager.execute_query(query, params, fetch=False)
            return True
            
        except Exception as e:
            raise DatabaseError(f"設定の保存に失敗しました: {str(e)}")
    
    def load_user_settings(self, setting_id: str) -> Optional[Dict[str, Any]]:
        """ユーザー設定の読み込み"""
        try:
            query = """
            SELECT selected_department, selected_model, selected_document_type, selected_doctor
            FROM app_settings
            WHERE setting_id = :setting_id
            """
            
            result = self.db_manager.execute_query(query, {"setting_id": setting_id})
            return result[0] if result else None
            
        except Exception as e:
            raise DatabaseError(f"設定の読み込みに失敗しました: {str(e)}")


# シングルトンインスタンス
statistics_queries = StatisticsQueries()
prompt_queries = PromptQueries()
settings_queries = SettingsQueries()