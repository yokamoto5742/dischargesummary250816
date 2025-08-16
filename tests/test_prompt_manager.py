import pytest
import datetime
from unittest.mock import patch, Mock, MagicMock
from sqlalchemy import text

from utils.prompt_manager import (
    get_prompt_collection,
    get_current_datetime,
    update_document,
    get_all_departments,
    get_all_prompts,
    create_or_update_prompt,
    delete_prompt,
    insert_document,
    initialize_default_prompt,
    get_prompt,
    initialize_database
)
from utils.exceptions import DatabaseError, AppError


class TestGetPromptCollection:
    """get_prompt_collection関数のテスト"""
    
    @patch('utils.prompt_manager.DatabaseManager')
    def test_get_prompt_collection_success(self, mock_db_manager):
        """正常にプロンプトコレクションを取得するテスト"""
        mock_instance = Mock()
        mock_db_manager.get_instance.return_value = mock_instance
        
        result = get_prompt_collection()
        
        assert result == mock_instance
        mock_db_manager.get_instance.assert_called_once()
    
    @patch('utils.prompt_manager.DatabaseManager')
    def test_get_prompt_collection_exception(self, mock_db_manager):
        """例外が発生した場合のテスト"""
        mock_db_manager.get_instance.side_effect = Exception("データベース接続エラー")
        
        with pytest.raises(DatabaseError, match="プロンプトコレクションの取得に失敗しました"):
            get_prompt_collection()


class TestGetCurrentDatetime:
    """get_current_datetime関数のテスト"""
    
    def test_get_current_datetime(self):
        """現在時刻の取得テスト"""
        with patch('utils.prompt_manager.datetime') as mock_datetime:
            mock_now = datetime.datetime(2024, 1, 1, 12, 0, 0)
            mock_datetime.datetime.now.return_value = mock_now
            
            result = get_current_datetime()
            
            assert result == mock_now
            mock_datetime.datetime.now.assert_called_once()


class TestUpdateDocument:
    """update_document関数のテスト"""
    
    def test_update_document_by_department(self, mock_database_manager):
        """部署での更新テスト"""
        query_dict = {"department": "内科"}
        update_data = {"name": "テスト名", "content": "テスト内容"}
        
        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            with patch('utils.prompt_manager.get_current_datetime') as mock_datetime:
                mock_now = datetime.datetime(2024, 1, 1, 12, 0, 0)
                mock_datetime.return_value = mock_now
                
                result = update_document(mock_database_manager, query_dict, update_data)
                
                assert result is True
                mock_database_manager.execute_query.assert_called_once()
                
                # 呼び出された引数を確認
                call_args = mock_database_manager.execute_query.call_args
                assert "UPDATE prompts" in call_args[0][0]
                assert call_args[1]["fetch"] is False
    
    def test_update_document_by_name(self, mock_database_manager):
        """名前での更新テスト"""
        query_dict = {"name": "テスト部署"}
        update_data = {"default_model": "gemini", "order_index": 1}
        
        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            with patch('utils.prompt_manager.get_current_datetime') as mock_datetime:
                mock_now = datetime.datetime(2024, 1, 1, 12, 0, 0)
                mock_datetime.return_value = mock_now
                
                result = update_document(mock_database_manager, query_dict, update_data)
                
                assert result is True
                mock_database_manager.execute_query.assert_called_once()
                
                call_args = mock_database_manager.execute_query.call_args
                assert "UPDATE departments" in call_args[0][0]
    
    def test_update_document_invalid_query(self, mock_database_manager):
        """無効なクエリでの更新テスト"""
        query_dict = {"invalid_key": "value"}
        update_data = {"content": "テスト"}
        
        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            with pytest.raises(DatabaseError, match="ドキュメントの更新に失敗しました"):
                update_document(mock_database_manager, query_dict, update_data)
    
    def test_update_document_database_error(self, mock_database_manager):
        """データベースエラーのテスト"""
        query_dict = {"department": "内科"}
        update_data = {"content": "テスト"}
        mock_database_manager.execute_query.side_effect = Exception("DB接続エラー")
        
        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            with pytest.raises(DatabaseError, match="ドキュメントの更新に失敗しました"):
                update_document(mock_database_manager, query_dict, update_data)


class TestGetAllDepartments:
    """get_all_departments関数のテスト"""
    
    @patch('utils.prompt_manager.DEFAULT_DEPARTMENT', ['内科', '外科', '小児科'])
    def test_get_all_departments(self):
        """全部署の取得テスト"""
        result = get_all_departments()
        assert result == ['内科', '外科', '小児科']


class TestGetAllPrompts:
    """get_all_prompts関数のテスト"""
    
    def test_get_all_prompts_success(self, mock_database_manager):
        """プロンプト一覧の正常取得テスト"""
        expected_prompts = [
            {"department": "内科", "content": "内科用プロンプト"},
            {"department": "外科", "content": "外科用プロンプト"}
        ]
        mock_database_manager.execute_query.return_value = expected_prompts
        
        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            result = get_all_prompts()
            
            assert result == expected_prompts
            mock_database_manager.execute_query.assert_called_once_with(
                "SELECT * FROM prompts ORDER BY department"
            )
    
    def test_get_all_prompts_database_error(self, mock_database_manager):
        """データベースエラーのテスト"""
        mock_database_manager.execute_query.side_effect = Exception("DB接続エラー")
        
        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            with pytest.raises(DatabaseError, match="プロンプト一覧の取得に失敗しました"):
                get_all_prompts()


class TestCreateOrUpdatePrompt:
    """create_or_update_prompt関数のテスト"""
    
    def test_create_or_update_prompt_update_existing(self, mock_database_manager):
        """既存プロンプトの更新テスト"""
        # 既存のプロンプトが存在する場合
        mock_database_manager.execute_query.side_effect = [
            [{"id": 1, "content": "既存プロンプト"}],  # 既存確認クエリ
            None  # 更新クエリ
        ]
        
        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            success, message = create_or_update_prompt(
                "内科", "主治医意見書", "田中医師", "新しいプロンプト", "gemini"
            )
            
            assert success is True
            assert message == "プロンプトを更新しました"
            assert mock_database_manager.execute_query.call_count == 2
    
    def test_create_or_update_prompt_create_new(self, mock_database_manager):
        """新規プロンプトの作成テスト"""
        # 既存のプロンプトが存在しない場合
        mock_database_manager.execute_query.side_effect = [
            [],  # 既存確認クエリ（空の結果）
            [{"id": 1}]  # 挿入クエリ
        ]
        
        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            with patch('utils.prompt_manager.insert_document', return_value=1) as mock_insert:
                success, message = create_or_update_prompt(
                    "内科", "主治医意見書", "田中医師", "新しいプロンプト", "gemini"
                )
                
                assert success is True
                assert message == "プロンプトを新規作成しました"
                mock_insert.assert_called_once()
    
    def test_create_or_update_prompt_invalid_input(self):
        """無効な入力のテスト"""
        success, message = create_or_update_prompt("", "", "", "")
        
        assert success is False
        assert message == "すべての項目を入力してください"
    
    def test_create_or_update_prompt_database_error(self, mock_database_manager):
        """データベースエラーのテスト"""
        mock_database_manager.execute_query.side_effect = DatabaseError("DB接続エラー")
        
        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            success, message = create_or_update_prompt(
                "内科", "主治医意見書", "田中医師", "新しいプロンプト"
            )
            
            assert success is False
            assert "DB接続エラー" in message


class TestDeletePrompt:
    """delete_prompt関数のテスト"""
    
    def test_delete_prompt_success(self, mock_database_manager):
        """プロンプト削除の成功テスト"""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result
        mock_database_manager.get_session.return_value = mock_session
        
        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            success, message = delete_prompt("内科", "主治医意見書", "田中医師")
            
            assert success is True
            assert message == "プロンプトを削除しました"
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    def test_delete_prompt_default_protection(self):
        """デフォルトプロンプトの削除保護テスト"""
        with patch('utils.prompt_manager.DEFAULT_DOCUMENT_TYPE', '主治医意見書'):
            success, message = delete_prompt("default", "主治医意見書", "default")

            assert success is False
            assert message == "デフォルトプロンプトは削除できません"
    
    def test_delete_prompt_not_found(self, mock_database_manager):
        """存在しないプロンプトの削除テスト"""
        mock_session = Mock()
        mock_result = Mock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result
        mock_database_manager.get_session.return_value = mock_session
        
        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            success, message = delete_prompt("内科", "主治医意見書", "田中医師")
            
            assert success is False
            assert message == "プロンプトが見つかりません"
            mock_session.rollback.assert_called_once()

    def test_delete_prompt_database_error(self, mock_database_manager):
        """データベースエラーのテスト"""
        mock_session = Mock()
        mock_session.execute.side_effect = Exception("DB接続エラー")
        mock_database_manager.get_session.return_value = mock_session

        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            # AppError例外がraiseされることを期待
            with pytest.raises(AppError, match="プロンプトの削除中にエラーが発生しました"):
                delete_prompt("内科", "主治医意見書", "田中医師")

            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()


class TestInsertDocument:
    """insert_document関数のテスト"""
    
    def test_insert_document_department(self, mock_database_manager):
        """部署の挿入テスト"""
        document = {
            "name": "新部署",
            "order_index": 1,
            "default_model": "gemini"
        }
        mock_database_manager.execute_query.return_value = [{"id": 1}]
        
        with patch('utils.prompt_manager.get_current_datetime') as mock_datetime:
            mock_now = datetime.datetime(2024, 1, 1, 12, 0, 0)
            mock_datetime.return_value = mock_now
            
            result = insert_document(mock_database_manager, document)
            
            assert result == 1
            mock_database_manager.execute_query.assert_called_once()
            
            call_args = mock_database_manager.execute_query.call_args
            assert "INSERT INTO departments" in call_args[0][0]
    
    def test_insert_document_prompt(self, mock_database_manager):
        """プロンプトの挿入テスト"""
        document = {
            "department": "内科",
            "doctor": "田中医師",
            "content": "プロンプト内容"
        }
        mock_database_manager.execute_query.return_value = [{"id": 1}]
        
        with patch('utils.prompt_manager.get_current_datetime') as mock_datetime:
            mock_now = datetime.datetime(2024, 1, 1, 12, 0, 0)
            mock_datetime.return_value = mock_now
            
            result = insert_document(mock_database_manager, document)
            
            assert result == 1
            mock_database_manager.execute_query.assert_called_once()
            
            call_args = mock_database_manager.execute_query.call_args
            assert "INSERT INTO prompts" in call_args[0][0]
    
    def test_insert_document_invalid_format(self, mock_database_manager):
        """無効なドキュメント形式のテスト"""
        document = {"invalid_key": "value"}
        
        with patch('utils.prompt_manager.get_current_datetime'):
            with pytest.raises(DatabaseError, match="ドキュメントの挿入に失敗しました"):
                insert_document(mock_database_manager, document)


class TestGetPrompt:
    """get_prompt関数のテスト"""
    
    def test_get_prompt_found(self, mock_database_manager):
        """プロンプトが見つかった場合のテスト"""
        expected_prompt = {
            "id": 1,
            "department": "内科",
            "document_type": "主治医意見書",
            "doctor": "田中医師",
            "content": "内科用プロンプト"
        }
        mock_database_manager.execute_query.return_value = [expected_prompt]
        
        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            result = get_prompt("内科", "主治医意見書", "田中医師")
            
            assert result == expected_prompt
            mock_database_manager.execute_query.assert_called_once()
    
    def test_get_prompt_fallback_to_default(self, mock_database_manager):
        """デフォルトプロンプトにフォールバックするテスト"""
        default_prompt = {
            "id": 1,
            "department": "default",
            "document_type": "主治医意見書",
            "doctor": "default",
            "content": "デフォルトプロンプト"
        }
        
        # 最初のクエリは空、2番目のクエリでデフォルトを返す
        mock_database_manager.execute_query.side_effect = [[], [default_prompt]]
        
        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            with patch('utils.prompt_manager.DEFAULT_DOCUMENT_TYPE', '主治医意見書'):
                result = get_prompt("存在しない部署", "主治医意見書", "存在しない医師")
                
                assert result == default_prompt
                assert mock_database_manager.execute_query.call_count == 2
    
    def test_get_prompt_no_default_found(self, mock_database_manager):
        """デフォルトプロンプトも見つからない場合のテスト"""
        mock_database_manager.execute_query.return_value = []
        
        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            result = get_prompt("存在しない部署", "存在しない文書", "存在しない医師")
            
            assert result is None
    
    def test_get_prompt_database_error(self, mock_database_manager):
        """データベースエラーのテスト"""
        mock_database_manager.execute_query.side_effect = Exception("DB接続エラー")
        
        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            with pytest.raises(DatabaseError, match="プロンプトの取得に失敗しました"):
                get_prompt("内科", "主治医意見書", "田中医師")


class TestInitializeDefaultPrompt:
    """initialize_default_prompt関数のテスト"""
    
    def test_initialize_default_prompt_not_exists(self, mock_database_manager):
        """デフォルトプロンプトが存在しない場合のテスト"""
        # 最初のクエリは空の結果（デフォルトプロンプトが存在しない）
        mock_database_manager.execute_query.return_value = []
        
        mock_config = Mock()
        mock_config.__getitem__ = Mock(return_value={'summary': 'デフォルトプロンプト内容'})
        
        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            with patch('utils.prompt_manager.get_config', return_value=mock_config):
                with patch('utils.prompt_manager.insert_document') as mock_insert:
                    with patch('utils.prompt_manager.DEFAULT_DOCUMENT_TYPE', '主治医意見書'):
                        initialize_default_prompt()
                        
                        mock_insert.assert_called_once()
                        insert_args = mock_insert.call_args[0][1]
                        assert insert_args['department'] == 'default'
                        assert insert_args['document_type'] == '主治医意見書'
                        assert insert_args['doctor'] == 'default'
                        assert insert_args['is_default'] is True
    
    def test_initialize_default_prompt_already_exists(self, mock_database_manager):
        """デフォルトプロンプトが既に存在する場合のテスト"""
        existing_prompt = [{"id": 1, "content": "既存プロンプト"}]
        mock_database_manager.execute_query.return_value = existing_prompt
        
        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            with patch('utils.prompt_manager.insert_document') as mock_insert:
                with patch('utils.prompt_manager.DEFAULT_DOCUMENT_TYPE', '主治医意見書'):
                    initialize_default_prompt()
                    
                    # insert_documentが呼ばれないことを確認
                    mock_insert.assert_not_called()
    
    def test_initialize_default_prompt_error(self, mock_database_manager):
        """初期化中にエラーが発生した場合のテスト"""
        mock_database_manager.execute_query.side_effect = Exception("DB接続エラー")
        
        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            with pytest.raises(DatabaseError, match="デフォルトプロンプトの初期化に失敗しました"):
                initialize_default_prompt()


class TestInitializeDatabase:
    """initialize_database関数のテスト"""
    
    @patch('utils.prompt_manager.init_schema')
    @patch('utils.prompt_manager.initialize_default_prompt')
    def test_initialize_database_success(self, mock_init_default, mock_init_schema, mock_database_manager):
        """データベース初期化の成功テスト"""
        mock_config = Mock()
        mock_config.__getitem__ = Mock(return_value={'summary': 'デフォルトプロンプト内容'})
        
        # 既存プロンプトが存在しない場合をシミュレート
        mock_database_manager.execute_query.return_value = []
        
        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            with patch('utils.prompt_manager.get_config', return_value=mock_config):
                with patch('utils.prompt_manager.DEFAULT_DEPARTMENT', ['内科']):
                    with patch('utils.prompt_manager.DOCUMENT_TYPES', ['主治医意見書']):
                        with patch('utils.prompt_manager.DEPARTMENT_DOCTORS_MAPPING', {'内科': ['田中医師']}):
                            with patch('utils.prompt_manager.insert_document') as mock_insert:
                                initialize_database()
                                
                                # スキーマ初期化とデフォルトプロンプト初期化が呼ばれることを確認
                                mock_init_schema.assert_called_once()
                                mock_init_default.assert_called_once()
                                
                                # 新しいプロンプトが挿入されることを確認
                                mock_insert.assert_called()
    
    @patch('utils.prompt_manager.init_schema')
    @patch('utils.prompt_manager.initialize_default_prompt')
    def test_initialize_database_existing_prompts(self, mock_init_default, mock_init_schema, mock_database_manager):
        """既存プロンプトがある場合のテスト"""
        # 既存プロンプトが存在する場合をシミュレート
        existing_prompt = [{"id": 1, "content": "既存プロンプト"}]
        mock_database_manager.execute_query.return_value = existing_prompt
        
        with patch('utils.prompt_manager.get_prompt_collection', return_value=mock_database_manager):
            with patch('utils.prompt_manager.DEFAULT_DEPARTMENT', ['内科']):
                with patch('utils.prompt_manager.DOCUMENT_TYPES', ['主治医意見書']):
                    with patch('utils.prompt_manager.DEPARTMENT_DOCTORS_MAPPING', {'内科': ['田中医師']}):
                        with patch('utils.prompt_manager.insert_document') as mock_insert:
                            initialize_database()
                            
                            # 既存プロンプトがあるため、新しい挿入は行われない
                            mock_insert.assert_not_called()
    
    @patch('utils.prompt_manager.init_schema')
    def test_initialize_database_error(self, mock_init_schema):
        """初期化中にエラーが発生した場合のテスト"""
        mock_init_schema.side_effect = Exception("スキーマ初期化エラー")
        
        with pytest.raises(DatabaseError, match="データベースの初期化に失敗しました"):
            initialize_database()
