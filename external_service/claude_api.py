import os
from typing import Tuple

from anthropic import AnthropicBedrock
from dotenv import load_dotenv

from external_service.base_api import BaseAPIClient
from utils.config import CLAUDE_MODEL
from utils.constants import MESSAGES
from utils.exceptions import APIError

load_dotenv()


class ClaudeAPIClient(BaseAPIClient):
    def __init__(self):
        # AWS認証情報を環境変数から取得
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")  # デフォルトリージョン

        # Bedrock用のモデル名を環境変数から取得（既存のCLAUDE_MODELをフォールバック）
        self.bedrock_model = os.getenv("ANTHROPIC_MODEL", CLAUDE_MODEL)

        # AWS認証情報が存在する場合、それをapi_keyとして扱う（互換性のため）
        api_key = "bedrock" if all([self.aws_access_key_id, self.aws_secret_access_key]) else None

        super().__init__(api_key, self.bedrock_model)
        self.client = None

    def initialize(self) -> bool:
        try:
            # AWS認証情報の確認
            if not all([self.aws_access_key_id, self.aws_secret_access_key, self.aws_region]):
                raise APIError("AWS認証情報が設定されていません。環境変数を確認してください。")

            # AnthropicBedrockクライアントの初期化
            self.client = AnthropicBedrock(
                aws_access_key=self.aws_access_key_id,
                aws_secret_key=self.aws_secret_access_key,
                aws_region=self.aws_region,
            )
            return True

        except Exception as e:
            raise APIError(f"Claude Bedrock API初期化エラー: {str(e)}")

    def _generate_content(self, prompt: str, model_name: str) -> Tuple[str, int, int]:
        """
        Amazon Bedrock経由でClaudeを使用してコンテンツを生成

        Args:
            prompt: 生成用のプロンプト
            model_name: 使用するモデル名

        Returns:
            生成されたテキスト、入力トークン数、出力トークン数のタプル
        """
        try:
            # Bedrockのモデル名を使用（環境変数で指定されたものか、引数で渡されたもの）
            bedrock_model_name = model_name if model_name else self.bedrock_model

            response = self.client.messages.create(
                model=bedrock_model_name,
                max_tokens=6000,  # 最大出力トークン数
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            if response.content:
                summary_text = response.content[0].text
            else:
                summary_text = "レスポンスが空です"

            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            return summary_text, input_tokens, output_tokens

        except Exception as e:
            raise APIError(f"Claude Bedrock API実行エラー: {str(e)}")
