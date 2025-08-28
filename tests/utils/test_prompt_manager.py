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

    # === 詳細なget_prompt()階層テスト ===
    
    def test_get_prompt_hierarchy_specific_department_doctor_document(self):
        """特定の部門・医師・文書タイプの階層テスト"""
        mock_prompt = Mock()
        mock_prompt.id = 100
        mock_prompt.department = "循環器内科"
        mock_prompt.document_type = "心エコー記録"
        mock_prompt.doctor = "心臓専門医"
        mock_prompt.content = "循環器内科心エコー専用プロンプト"
        mock_prompt.selected_model = "claude"
        mock_prompt.is_default = False
        mock_prompt.created_at = datetime.datetime(2024, 3, 15)
        mock_prompt.updated_at = datetime.datetime(2024, 3, 16)
        
        self.mock_repo.get_by_keys.return_value = mock_prompt
        
        result = self.prompt_manager.get_prompt("循環器内科", "心エコー記録", "心臓専門医")
        
        assert result['department'] == "循環器内科"
        assert result['document_type'] == "心エコー記録"
        assert result['doctor'] == "心臓専門医"
        assert result['content'] == "循環器内科心エコー専用プロンプト"
        assert result['selected_model'] == "claude"
        assert result['is_default'] is False
        
        self.mock_repo.get_by_keys.assert_called_once_with("循環器内科", "心エコー記録", "心臓専門医")
        self.mock_repo.get_default_prompt.assert_not_called()

    def test_get_prompt_hierarchy_fallback_scenarios(self):
        """階層フォールバック各種シナリオのテスト"""
        # シナリオ1: 特定プロンプトなし → デフォルトプロンプトあり
        self.mock_repo.get_by_keys.return_value = None
        
        mock_default_prompt = Mock()
        mock_default_prompt.id = 1
        mock_default_prompt.department = "default"
        mock_default_prompt.document_type = "退院時サマリ"
        mock_default_prompt.doctor = "default"
        mock_default_prompt.content = "汎用デフォルトプロンプト"
        mock_default_prompt.selected_model = None
        mock_default_prompt.is_default = True
        mock_default_prompt.created_at = datetime.datetime(2024, 1, 1)
        mock_default_prompt.updated_at = datetime.datetime(2024, 1, 1)
        
        self.mock_repo.get_default_prompt.return_value = mock_default_prompt
        
        result = self.prompt_manager.get_prompt("存在しない科", "存在しない文書", "存在しない医師")
        
        assert result['id'] == 1
        assert result['department'] == "default"
        assert result['document_type'] == "退院時サマリ"
        assert result['doctor'] == "default"
        assert result['content'] == "汎用デフォルトプロンプト"
        assert result['selected_model'] is None
        assert result['is_default'] is True
        
        self.mock_repo.get_by_keys.assert_called_once_with("存在しない科", "存在しない文書", "存在しない医師")
        self.mock_repo.get_default_prompt.assert_called_once()

    def test_get_prompt_hierarchy_complete_fallthrough(self):
        """完全なフォールスルー（プロンプトが全く見つからない）のテスト"""
        self.mock_repo.get_by_keys.return_value = None
        self.mock_repo.get_default_prompt.return_value = None
        
        result = self.prompt_manager.get_prompt("新設科", "新文書タイプ", "新任医師")
        
        assert result is None
        
        self.mock_repo.get_by_keys.assert_called_once_with("新設科", "新文書タイプ", "新任医師")
        self.mock_repo.get_default_prompt.assert_called_once()

    def test_get_prompt_with_model_selection_hierarchy(self):
        """モデル選択を含む階層テスト"""
        # 特定プロンプトでモデルが指定されている場合
        mock_prompt_with_model = Mock()
        mock_prompt_with_model.id = 50
        mock_prompt_with_model.department = "放射線科"
        mock_prompt_with_model.document_type = "CT読影報告"
        mock_prompt_with_model.doctor = "放射線専門医"
        mock_prompt_with_model.content = "CT読影専用プロンプト"
        mock_prompt_with_model.selected_model = "gemini"
        mock_prompt_with_model.is_default = False
        mock_prompt_with_model.created_at = datetime.datetime(2024, 2, 10)
        mock_prompt_with_model.updated_at = datetime.datetime(2024, 2, 12)
        
        self.mock_repo.get_by_keys.return_value = mock_prompt_with_model
        
        result = self.prompt_manager.get_prompt("放射線科", "CT読影報告", "放射線専門医")
        
        assert result['selected_model'] == "gemini"
        assert result['content'] == "CT読影専用プロンプト"
        assert result['is_default'] is False

    def test_get_prompt_with_null_model_selection(self):
        """モデル選択がNullの場合のテスト"""
        mock_prompt_no_model = Mock()
        mock_prompt_no_model.id = 75
        mock_prompt_no_model.department = "整形外科"
        mock_prompt_no_model.document_type = "手術記録"
        mock_prompt_no_model.doctor = "整形外科医師"
        mock_prompt_no_model.content = "整形外科手術記録プロンプト"
        mock_prompt_no_model.selected_model = None
        mock_prompt_no_model.is_default = False
        mock_prompt_no_model.created_at = datetime.datetime(2024, 4, 1)
        mock_prompt_no_model.updated_at = datetime.datetime(2024, 4, 5)
        
        self.mock_repo.get_by_keys.return_value = mock_prompt_no_model
        
        result = self.prompt_manager.get_prompt("整形外科", "手術記録", "整形外科医師")
        
        assert result['selected_model'] is None
        assert result['content'] == "整形外科手術記録プロンプト"

    def test_get_prompt_japanese_medical_terms(self):
        """日本語医療用語でのプロンプト取得テスト"""
        mock_prompt = Mock()
        mock_prompt.id = 200
        mock_prompt.department = "消化器内科"
        mock_prompt.document_type = "内視鏡検査報告書"
        mock_prompt.doctor = "内視鏡専門医"
        mock_prompt.content = "内視鏡検査用の詳細な記録プロンプト\n所見、診断、治療方針を含む"
        mock_prompt.selected_model = "claude"
        mock_prompt.is_default = False
        mock_prompt.created_at = datetime.datetime(2024, 5, 10)
        mock_prompt.updated_at = datetime.datetime(2024, 5, 15)
        
        self.mock_repo.get_by_keys.return_value = mock_prompt
        
        result = self.prompt_manager.get_prompt("消化器内科", "内視鏡検査報告書", "内視鏡専門医")
        
        assert result['department'] == "消化器内科"
        assert result['document_type'] == "内視鏡検査報告書"
        assert result['doctor'] == "内視鏡専門医"
        assert "内視鏡検査用の詳細な記録プロンプト" in result['content']
        assert "所見、診断、治療方針を含む" in result['content']

    def test_get_prompt_edge_case_empty_strings(self):
        """空文字列パラメータのエッジケーステスト"""
        self.mock_repo.get_by_keys.return_value = None
        self.mock_repo.get_default_prompt.return_value = None
        
        result = self.prompt_manager.get_prompt("", "", "")
        
        assert result is None
        self.mock_repo.get_by_keys.assert_called_once_with("", "", "")

    def test_get_prompt_edge_case_special_characters(self):
        """特殊文字を含むパラメータのテスト"""
        mock_prompt = Mock()
        mock_prompt.id = 300
        mock_prompt.department = "特殊診療科@＃"
        mock_prompt.document_type = "特殊記録/＼"
        mock_prompt.doctor = "専門医_TEST"
        mock_prompt.content = "特殊文字対応プロンプト"
        mock_prompt.selected_model = "claude"
        mock_prompt.is_default = False
        mock_prompt.created_at = datetime.datetime(2024, 6, 1)
        mock_prompt.updated_at = datetime.datetime(2024, 6, 2)
        
        self.mock_repo.get_by_keys.return_value = mock_prompt
        
        result = self.prompt_manager.get_prompt("特殊診療科@＃", "特殊記録/＼", "専門医_TEST")
        
        assert result['department'] == "特殊診療科@＃"
        assert result['document_type'] == "特殊記録/＼"
        assert result['doctor'] == "専門医_TEST"

    def test_get_prompt_repository_method_call_sequence(self):
        """リポジトリメソッド呼び出し順序のテスト"""
        # 最初の呼び出しでは特定プロンプトが見つからない
        self.mock_repo.get_by_keys.return_value = None
        
        # デフォルトプロンプトが見つかる
        mock_default = Mock()
        mock_default.id = 1
        mock_default.department = "default"
        mock_default.document_type = "退院時サマリ"
        mock_default.doctor = "default"
        mock_default.content = "デフォルト"
        mock_default.selected_model = None
        mock_default.is_default = True
        mock_default.created_at = datetime.datetime(2024, 1, 1)
        mock_default.updated_at = datetime.datetime(2024, 1, 1)
        
        self.mock_repo.get_default_prompt.return_value = mock_default
        
        result = self.prompt_manager.get_prompt("テスト科", "テスト文書", "テスト医師")
        
        # 呼び出し順序を確認
        call_order = [call[0] for call in self.mock_repo.method_calls]
        expected_order = ['get_by_keys', 'get_default_prompt']
        
        for i, expected_method in enumerate(expected_order):
            assert call_order[i] == expected_method
        
        assert result['department'] == "default"