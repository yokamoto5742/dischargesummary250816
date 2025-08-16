from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class AppSetting(Base):
    __tablename__ = 'app_settings'

    id = Column(Integer, primary_key=True)
    setting_id = Column(String(100), nullable=False)
    app_type = Column(String(50), nullable=False)
    selected_department = Column(String(100))
    selected_model = Column(String(50))
    selected_document_type = Column(String(100))
    selected_doctor = Column(String(100))
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('setting_id', 'app_type', name='unique_setting_per_app'),
    )


class Prompt(Base):
    __tablename__ = 'prompts'

    id = Column(Integer, primary_key=True)
    department = Column(String(100), nullable=False)
    document_type = Column(String(100), nullable=False)
    doctor = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    selected_model = Column(String(50))
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


class SummaryUsage(Base):
    __tablename__ = 'summary_usage'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime(timezone=True), default=func.now())
    app_type = Column(String(50))
    document_types = Column(String(100))
    model_detail = Column(String(100))
    department = Column(String(100))
    doctor = Column(String(100))
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    total_tokens = Column(Integer)
    processing_time = Column(Integer)
