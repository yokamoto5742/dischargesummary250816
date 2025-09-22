import datetime
from typing import Dict, List, Any, Optional, Tuple

from sqlalchemy import func, desc
from sqlalchemy.orm import sessionmaker

from database.models import AppSetting, Prompt, SummaryUsage
from utils.exceptions import DatabaseError


class BaseRepository:

    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory

    def get_session(self):
        return self.session_factory()


class PromptRepository(BaseRepository):

    def get_by_keys(self, department: str, document_type: str, doctor: str) -> Optional[Prompt]:
        try:
            with self.get_session() as session:
                return session.query(Prompt).filter(
                    Prompt.department == department,
                    Prompt.document_type == document_type,
                    Prompt.doctor == doctor
                ).first()
        except Exception as e:
            raise DatabaseError(f"プロンプトの取得に失敗しました: {str(e)}")

    def get_default_prompt(self) -> Optional[Prompt]:
        try:
            with self.get_session() as session:
                return session.query(Prompt).filter(
                    Prompt.department == "default",
                    Prompt.is_default == True
                ).first()
        except Exception as e:
            raise DatabaseError(f"デフォルトプロンプトの取得に失敗しました: {str(e)}")

    def create_or_update(self, department: str, document_type: str, doctor: str,
                        content: str, selected_model: Optional[str] = None) -> Tuple[bool, str]:
        try:
            with self.get_session() as session:
                existing_prompt = session.query(Prompt).filter(
                    Prompt.department == department,
                    Prompt.document_type == document_type,
                    Prompt.doctor == doctor
                ).first()

                is_update = existing_prompt is not None

                if existing_prompt:
                    existing_prompt.content = content
                    existing_prompt.selected_model = selected_model
                    existing_prompt.updated_at = datetime.datetime.now()
                else:
                    new_prompt = Prompt(
                        department=department,
                        document_type=document_type,
                        doctor=doctor,
                        content=content,
                        selected_model=selected_model,
                        is_default=False
                    )
                    session.add(new_prompt)

                session.commit()
                action = "更新" if is_update else "新規作成"
                return True, f"プロンプトを{action}しました"

        except Exception as e:
            raise DatabaseError(f"プロンプトの作成/更新に失敗しました: {str(e)}")

    def delete_by_keys(self, department: str, document_type: str, doctor: str) -> Tuple[bool, str]:
        try:
            with self.get_session() as session:
                prompt = session.query(Prompt).filter(
                    Prompt.department == department,
                    Prompt.document_type == document_type,
                    Prompt.doctor == doctor
                ).first()

                if not prompt:
                    return False, "プロンプトが見つかりません"

                if prompt.is_default and department == "default":
                    return False, "デフォルトプロンプトは削除できません"

                session.delete(prompt)
                session.commit()
                return True, "プロンプトを削除しました"

        except Exception as e:
            raise DatabaseError(f"プロンプトの削除に失敗しました: {str(e)}")

    def get_all(self) -> List[Prompt]:
        try:
            with self.get_session() as session:
                return session.query(Prompt).order_by(
                    Prompt.department,
                    Prompt.document_type,
                    Prompt.doctor
                ).all()
        except Exception as e:
            raise DatabaseError(f"プロンプト一覧の取得に失敗しました: {str(e)}")

    def create_default_prompt(self, content: str) -> None:
        try:
            with self.get_session() as session:
                existing = session.query(Prompt).filter(
                    Prompt.department == "default",
                    Prompt.is_default == True
                ).first()

                if not existing:
                    default_prompt = Prompt(
                        department="default",
                        document_type="退院時サマリ",
                        doctor="default",
                        content=content,
                        is_default=True
                    )
                    session.add(default_prompt)
                    session.commit()

        except Exception as e:
            raise DatabaseError(f"デフォルトプロンプトの作成に失敗しました: {str(e)}")

    def bulk_create_prompts(self, prompts_data: List[Dict[str, Any]]) -> None:
        try:
            with self.get_session() as session:
                for data in prompts_data:
                    existing = session.query(Prompt).filter(
                        Prompt.department == data['department'],
                        Prompt.document_type == data['document_type'],
                        Prompt.doctor == data['doctor']
                    ).first()

                    if not existing:
                        prompt = Prompt(**data)
                        session.add(prompt)

                session.commit()

        except Exception as e:
            raise DatabaseError(f"プロンプトの一括作成に失敗しました: {str(e)}")


class UsageStatisticsRepository(BaseRepository):

    def save_usage(self, usage_data: Dict[str, Any]) -> None:
        try:
            with self.get_session() as session:
                usage = SummaryUsage(**usage_data)
                session.add(usage)
                session.commit()

        except Exception as e:
            raise DatabaseError(f"使用統計の保存に失敗しました: {str(e)}")

    def _apply_date_filter(self, query, start_date: datetime.datetime, end_date: datetime.datetime):
        return query.filter(
            SummaryUsage.date >= start_date,
            SummaryUsage.date <= end_date
        )

    def _apply_model_filter(self, query, model_filter: Optional[str]):
        if not model_filter or model_filter == "すべて":
            return query

        if model_filter == "Gemini_Pro":
            return query.filter(
                SummaryUsage.model_detail.ilike('%gemini%'),
                ~SummaryUsage.model_detail.ilike('%flash%')
            )
        elif model_filter == "Gemini_Flash":
            return query.filter(SummaryUsage.model_detail.ilike('%flash%'))
        elif model_filter == "Claude":
            return query.filter(SummaryUsage.model_detail.ilike('%claude%'))

        return query

    def apply_document_type_filter(self, query, document_type_filter: Optional[str]):
        if not document_type_filter or document_type_filter == "すべて":
            return query

        return query.filter(SummaryUsage.document_types == document_type_filter)

    def _apply_filters(self, query, start_date: datetime.datetime, end_date: datetime.datetime,
                       model_filter: Optional[str] = None, document_type_filter: Optional[str] = None):
        query = self._apply_date_filter(query, start_date, end_date)
        query = self._apply_model_filter(query, model_filter)
        query = self._apply_document_type_filter(query, document_type_filter)
        return query

    def get_usage_summary(self, start_date: datetime.datetime, end_date: datetime.datetime,
                          model_filter: Optional[str] = None,
                          document_type_filter: Optional[str] = None) -> Dict[str, Any]:
        try:
            with self.get_session() as session:
                query = session.query(
                    func.count(SummaryUsage.id).label('count'),
                    func.sum(SummaryUsage.input_tokens).label('total_input_tokens'),
                    func.sum(SummaryUsage.output_tokens).label('total_output_tokens'),
                    func.sum(SummaryUsage.total_tokens).label('total_tokens')
                )

                query = self._apply_filters(query, start_date, end_date, model_filter, document_type_filter)

                result = query.first()
                return {
                    'count': result.count or 0,
                    'total_input_tokens': result.total_input_tokens or 0,
                    'total_output_tokens': result.total_output_tokens or 0,
                    'total_tokens': result.total_tokens or 0
                }

        except Exception as e:
            raise DatabaseError(f"使用統計の取得に失敗しました: {str(e)}")

    def get_department_statistics(self, start_date: datetime.datetime, end_date: datetime.datetime,
                                  model_filter: Optional[str] = None,
                                  document_type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            with self.get_session() as session:
                query = session.query(
                    func.coalesce(SummaryUsage.department, 'default').label('department'),
                    func.coalesce(SummaryUsage.doctor, 'default').label('doctor'),
                    SummaryUsage.document_types,
                    func.count(SummaryUsage.id).label('count'),
                    func.sum(SummaryUsage.input_tokens).label('input_tokens'),
                    func.sum(SummaryUsage.output_tokens).label('output_tokens'),
                    func.sum(SummaryUsage.total_tokens).label('total_tokens'),
                    func.sum(SummaryUsage.processing_time).label('processing_time')
                )

                query = self._apply_filters(query, start_date, end_date, model_filter, document_type_filter)

                query = query.group_by(
                    SummaryUsage.department,
                    SummaryUsage.doctor,
                    SummaryUsage.document_types
                ).order_by(desc(func.count(SummaryUsage.id)))

                results = query.all()
                return [
                    {
                        'department': r.department,
                        'doctor': r.doctor,
                        'document_types': r.document_types,
                        'count': r.count,
                        'input_tokens': r.input_tokens,
                        'output_tokens': r.output_tokens,
                        'total_tokens': r.total_tokens,
                        'processing_time': r.processing_time
                    }
                    for r in results
                ]

        except Exception as e:
            raise DatabaseError(f"部門別統計の取得に失敗しました: {str(e)}")

    def get_usage_records(self, start_date: datetime.datetime, end_date: datetime.datetime,
                          model_filter: Optional[str] = None,
                          document_type_filter: Optional[str] = None) -> List[SummaryUsage]:
        try:
            with self.get_session() as session:
                query = session.query(SummaryUsage)
                query = self._apply_filters(query, start_date, end_date, model_filter, document_type_filter)
                return query.order_by(desc(SummaryUsage.date)).all()

        except Exception as e:
            raise DatabaseError(f"使用記録の取得に失敗しました: {str(e)}")


class SettingsRepository(BaseRepository):

    def save_user_settings(self, setting_id: str, app_type: str,
                          department: str, model: str, document_type: str, doctor: str) -> None:
        try:
            with self.get_session() as session:
                existing = session.query(AppSetting).filter(
                    AppSetting.setting_id == setting_id,
                    AppSetting.app_type == app_type
                ).first()

                if existing:
                    existing.selected_department = department
                    existing.selected_model = model
                    existing.selected_document_type = document_type
                    existing.selected_doctor = doctor
                    existing.updated_at = datetime.datetime.now()
                else:
                    new_setting = AppSetting(
                        setting_id=setting_id,
                        app_type=app_type,
                        selected_department=department,
                        selected_model=model,
                        selected_document_type=document_type,
                        selected_doctor=doctor
                    )
                    session.add(new_setting)

                session.commit()

        except Exception as e:
            raise DatabaseError(f"設定の保存に失敗しました: {str(e)}")

    def load_user_settings(self, setting_id: str) -> Optional[AppSetting]:
        try:
            with self.get_session() as session:
                return session.query(AppSetting).filter(
                    AppSetting.setting_id == setting_id
                ).first()

        except Exception as e:
            raise DatabaseError(f"設定の読み込みに失敗しました: {str(e)}")

    def get_settings_by_app_type(self, app_type: Optional[str] = None) -> List[AppSetting]:
        try:
            with self.get_session() as session:
                query = session.query(AppSetting)
                if app_type:
                    query = query.filter(AppSetting.app_type == app_type)
                return query.all()

        except Exception as e:
            raise DatabaseError(f"設定の取得に失敗しました: {str(e)}")
