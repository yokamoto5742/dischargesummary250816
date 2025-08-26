import datetime
from unittest.mock import Mock, patch

import pytest

from database.repositories import PromptRepository
from utils.exceptions import DatabaseError, AppError
from utils.prompt_manager import PromptManager, get_prompt_manager


class TestPromptManager:
    
    def setup_method(self):
        with patch('utils.prompt_manager.get_prompt_repository') as mock_get_repo, \
             patch('utils.prompt_manager.get_config') as mock_get_config:
            
            mock_repo = Mock(spec=PromptRepository)
            mock_get_repo.return_value = mock_repo
            mock_config = {'PROMPTS': {'summary': 'Default prompt content'}}
            mock_get_config.return_value = mock_config
            
            self.prompt_manager = PromptManager()
            self.mock_repo = mock_repo

    def test_init(self):
        with patch('utils.prompt_manager.get_prompt_repository') as mock_get_repo, \
             patch('utils.prompt_manager.get_config') as mock_get_config:
            
            mock_repo = Mock(spec=PromptRepository)
            mock_get_repo.return_value = mock_repo
            mock_config = {'PROMPTS': {'summary': 'Test prompt'}}
            mock_get_config.return_value = mock_config
            
            pm = PromptManager()
            
            assert pm.prompt_repository is mock_repo
            assert pm.default_prompt_content == 'Test prompt'
            mock_get_repo.assert_called_once()
            mock_get_config.assert_called_once()

    def test_get_prompt_success(self):
        mock_prompt = Mock()
        mock_prompt.id = 1
        mock_prompt.department = "dept"
        mock_prompt.document_type = "doc_type"
        mock_prompt.doctor = "doctor"
        mock_prompt.content = "prompt content"
        mock_prompt.selected_model = "model"
        mock_prompt.is_default = False
        mock_prompt.created_at = datetime.datetime(2023, 1, 1)
        mock_prompt.updated_at = datetime.datetime(2023, 1, 2)
        
        self.mock_repo.get_by_keys.return_value = mock_prompt
        
        result = self.prompt_manager.get_prompt("dept", "doc_type", "doctor")
        
        expected = {
            'id': 1,
            'department': "dept",
            'document_type': "doc_type",
            'doctor': "doctor",
            'content': "prompt content",
            'selected_model': "model",
            'is_default': False,
            'created_at': datetime.datetime(2023, 1, 1),
            'updated_at': datetime.datetime(2023, 1, 2)
        }
        
        assert result == expected
        self.mock_repo.get_by_keys.assert_called_once_with("dept", "doc_type", "doctor")

    def test_get_prompt_fallback_to_default(self):
        mock_default_prompt = Mock()
        mock_default_prompt.id = 1
        mock_default_prompt.department = "default"
        mock_default_prompt.document_type = "退院時サマリ"
        mock_default_prompt.doctor = "default"
        mock_default_prompt.content = "default content"
        mock_default_prompt.selected_model = None
        mock_default_prompt.is_default = True
        mock_default_prompt.created_at = datetime.datetime(2023, 1, 1)
        mock_default_prompt.updated_at = datetime.datetime(2023, 1, 1)
        
        self.mock_repo.get_by_keys.return_value = None
        self.mock_repo.get_default_prompt.return_value = mock_default_prompt
        
        result = self.prompt_manager.get_prompt("dept", "doc_type", "doctor")
        
        expected = {
            'id': 1,
            'department': "default",
            'document_type': "退院時サマリ",
            'doctor': "default",
            'content': "default content",
            'selected_model': None,
            'is_default': True,
            'created_at': datetime.datetime(2023, 1, 1),
            'updated_at': datetime.datetime(2023, 1, 1)
        }
        
        assert result == expected
        self.mock_repo.get_by_keys.assert_called_once_with("dept", "doc_type", "doctor")
        self.mock_repo.get_default_prompt.assert_called_once()

    def test_get_prompt_no_prompt_found(self):
        self.mock_repo.get_by_keys.return_value = None
        self.mock_repo.get_default_prompt.return_value = None
        
        result = self.prompt_manager.get_prompt("dept", "doc_type", "doctor")
        
        assert result is None

    @patch('utils.prompt_manager.DEFAULT_DOCUMENT_TYPE', '退院時サマリ')
    def test_get_prompt_default_parameters(self):
        self.mock_repo.get_by_keys.return_value = None
        self.mock_repo.get_default_prompt.return_value = None
        
        result = self.prompt_manager.get_prompt()
        
        assert result is None
        self.mock_repo.get_by_keys.assert_called_once_with("default", "退院時サマリ", "default")

    def test_get_prompt_database_error(self):
        self.mock_repo.get_by_keys.side_effect = DatabaseError("Database connection failed")
        
        with pytest.raises(DatabaseError) as exc_info:
            self.prompt_manager.get_prompt("dept", "doc_type", "doctor")
        assert "Database connection failed" in str(exc_info.value)

    def test_get_prompt_general_exception(self):
        self.mock_repo.get_by_keys.side_effect = Exception("Unexpected error")
        
        with pytest.raises(DatabaseError) as exc_info:
            self.prompt_manager.get_prompt("dept", "doc_type", "doctor")
        assert "プロンプトの取得に失敗しました" in str(exc_info.value)

    def test_create_or_update_prompt_success(self):
        self.mock_repo.create_or_update.return_value = (True, "作成しました")
        
        success, message = self.prompt_manager.create_or_update_prompt(
            "dept", "doc_type", "doctor", "content", "model"
        )
        
        assert success is True
        assert message == "作成しました"
        self.mock_repo.create_or_update.assert_called_once_with(
            "dept", "doc_type", "doctor", "content", "model"
        )

    def test_create_or_update_prompt_missing_fields(self):
        success, message = self.prompt_manager.create_or_update_prompt(
            "", "doc_type", "doctor", "content", "model"
        )
        
        assert success is False
        assert message == "すべての項目を入力してください"

    def test_create_or_update_prompt_database_error(self):
        self.mock_repo.create_or_update.side_effect = DatabaseError("Database error")
        
        success, message = self.prompt_manager.create_or_update_prompt(
            "dept", "doc_type", "doctor", "content", "model"
        )
        
        assert success is False
        assert message == "Database error"

    def test_create_or_update_prompt_general_exception(self):
        self.mock_repo.create_or_update.side_effect = Exception("Unexpected error")
        
        with pytest.raises(AppError) as exc_info:
            self.prompt_manager.create_or_update_prompt(
                "dept", "doc_type", "doctor", "content", "model"
            )
        assert "プロンプトの作成/更新中にエラーが発生しました" in str(exc_info.value)

    def test_delete_prompt_success(self):
        self.mock_repo.delete_by_keys.return_value = (True, "削除しました")
        
        success, message = self.prompt_manager.delete_prompt("dept", "doc_type", "doctor")
        
        assert success is True
        assert message == "削除しました"
        self.mock_repo.delete_by_keys.assert_called_once_with("dept", "doc_type", "doctor")

    @patch('utils.prompt_manager.DEFAULT_DOCUMENT_TYPE', '退院時サマリ')
    def test_delete_prompt_default_prompt_protection(self):
        success, message = self.prompt_manager.delete_prompt("default", "退院時サマリ", "default")
        
        assert success is False
        assert message == "デフォルトプロンプトは削除できません"
        self.mock_repo.delete_by_keys.assert_not_called()

    def test_delete_prompt_database_error(self):
        self.mock_repo.delete_by_keys.side_effect = DatabaseError("Database error")
        
        success, message = self.prompt_manager.delete_prompt("dept", "doc_type", "doctor")
        
        assert success is False
        assert message == "Database error"

    def test_delete_prompt_general_exception(self):
        self.mock_repo.delete_by_keys.side_effect = Exception("Unexpected error")
        
        with pytest.raises(AppError) as exc_info:
            self.prompt_manager.delete_prompt("dept", "doc_type", "doctor")
        assert "プロンプトの削除中にエラーが発生しました" in str(exc_info.value)

    def test_get_all_prompts_success(self):
        mock_prompts = [
            Mock(id=1, department="dept1", document_type="type1", doctor="doctor1",
                 content="content1", selected_model="model1", is_default=False,
                 created_at=datetime.datetime(2023, 1, 1),
                 updated_at=datetime.datetime(2023, 1, 2)),
            Mock(id=2, department="dept2", document_type="type2", doctor="doctor2",
                 content="content2", selected_model="model2", is_default=True,
                 created_at=datetime.datetime(2023, 2, 1),
                 updated_at=datetime.datetime(2023, 2, 2))
        ]
        
        self.mock_repo.get_all.return_value = mock_prompts
        
        result = self.prompt_manager.get_all_prompts()
        
        expected = [
            {
                'id': 1, 'department': "dept1", 'document_type': "type1",
                'doctor': "doctor1", 'content': "content1", 'selected_model': "model1",
                'is_default': False, 'created_at': datetime.datetime(2023, 1, 1),
                'updated_at': datetime.datetime(2023, 1, 2)
            },
            {
                'id': 2, 'department': "dept2", 'document_type': "type2",
                'doctor': "doctor2", 'content': "content2", 'selected_model': "model2",
                'is_default': True, 'created_at': datetime.datetime(2023, 2, 1),
                'updated_at': datetime.datetime(2023, 2, 2)
            }
        ]
        
        assert result == expected
        self.mock_repo.get_all.assert_called_once()

    def test_get_all_prompts_exception(self):
        self.mock_repo.get_all.side_effect = Exception("Database error")
        
        with pytest.raises(DatabaseError) as exc_info:
            self.prompt_manager.get_all_prompts()
        assert "プロンプト一覧の取得に失敗しました" in str(exc_info.value)

    def test_initialize_default_prompt_success(self):
        self.prompt_manager.initialize_default_prompt()
        
        self.mock_repo.create_default_prompt.assert_called_once_with('Default prompt content')

    def test_initialize_default_prompt_exception(self):
        self.mock_repo.create_default_prompt.side_effect = Exception("Database error")
        
        with pytest.raises(DatabaseError) as exc_info:
            self.prompt_manager.initialize_default_prompt()
        assert "デフォルトプロンプトの初期化に失敗しました" in str(exc_info.value)

    @patch('utils.prompt_manager.DEFAULT_DEPARTMENT', ['dept1', 'dept2'])
    @patch('utils.prompt_manager.DEPARTMENT_DOCTORS_MAPPING', {'dept1': ['doctor1'], 'dept2': ['doctor2', 'doctor3']})
    @patch('utils.prompt_manager.DOCUMENT_TYPES', ['type1', 'type2'])
    @patch('utils.prompt_manager.datetime')
    def test_initialize_all_prompts_success(self, mock_datetime):
        mock_now = datetime.datetime(2023, 1, 1, 12)
        mock_datetime.datetime.now.return_value = mock_now
        
        self.prompt_manager.initialize_all_prompts()
        
        self.mock_repo.bulk_create_prompts.assert_called_once()
        call_args = self.mock_repo.bulk_create_prompts.call_args[0][0]
        
        # Should create 6 prompts: 2 depts * (1+2) doctors * 2 types = 6
        assert len(call_args) == 6
        
        # Verify structure of first prompt
        first_prompt = call_args[0]
        expected_keys = {'department', 'document_type', 'doctor', 'content', 'is_default', 'created_at', 'updated_at'}
        assert set(first_prompt.keys()) == expected_keys
        assert first_prompt['is_default'] is False
        assert first_prompt['content'] == 'Default prompt content'

    def test_initialize_all_prompts_exception(self):
        with patch('utils.prompt_manager.DEFAULT_DEPARTMENT', ['dept1']), \
             patch('utils.prompt_manager.DOCUMENT_TYPES', ['type1']), \
             patch('utils.prompt_manager.DEPARTMENT_DOCTORS_MAPPING', {'dept1': ['doctor1']}):
            
            self.mock_repo.bulk_create_prompts.side_effect = Exception("Database error")
            
            with pytest.raises(DatabaseError) as exc_info:
                self.prompt_manager.initialize_all_prompts()
            assert "プロンプト初期化に失敗しました" in str(exc_info.value)


class TestGetPromptManager:
    
    def test_get_prompt_manager_singleton(self):
        # Reset the global variable
        import utils.prompt_manager
        utils.prompt_manager._prompt_manager = None
        
        with patch('utils.prompt_manager.PromptManager') as mock_pm_class:
            mock_instance = Mock()
            mock_pm_class.return_value = mock_instance
            
            # First call should create instance
            result1 = get_prompt_manager()
            assert result1 is mock_instance
            mock_pm_class.assert_called_once()
            
            # Second call should return same instance
            result2 = get_prompt_manager()
            assert result2 is mock_instance
            assert result1 is result2
            # Should not create new instance
            mock_pm_class.assert_called_once()

    def test_get_prompt_manager_initialization(self):
        # Reset the global variable
        import utils.prompt_manager
        utils.prompt_manager._prompt_manager = None
        
        result = get_prompt_manager()
        
        assert isinstance(result, PromptManager)
        
        # Test that subsequent calls return the same instance
        result2 = get_prompt_manager()
        assert result is result2