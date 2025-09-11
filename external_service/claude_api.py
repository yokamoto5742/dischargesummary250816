import os
from typing import Tuple

from anthropic import AnthropicBedrock
from dotenv import load_dotenv

from external_service.base_api import BaseAPIClient
from utils.config import CLAUDE_API_KEY, CLAUDE_MODEL
from utils.constants import MESSAGES
from utils.exceptions import APIError

load_dotenv()


class ClaudeAPIClient(BaseAPIClient):
    def __init__(self):
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")

        self.bedrock_model = os.getenv("ANTHROPIC_MODEL", CLAUDE_MODEL)

        super().__init__(CLAUDE_API_KEY, self.bedrock_model)
        self.client = None

    def initialize(self) -> bool:
        try:
            if not all([self.aws_access_key_id, self.aws_secret_access_key, self.aws_region]):
                raise APIError("AWS認証情報が設定されていません。環境変数を確認してください。")

            self.client = AnthropicBedrock(
                aws_access_key=self.aws_access_key_id,
                aws_secret_key=self.aws_secret_access_key,
                aws_region=self.aws_region,
            )
            return True

        except Exception:
            raise APIError(MESSAGES["API_CREDENTIALS_MISSING"])

    def _generate_content(self, prompt: str, model_name: str) -> Tuple[str, int, int]:
        try:
            bedrock_model_name = model_name if model_name else self.bedrock_model

            response = self.client.messages.create(
                model=bedrock_model_name,
                max_tokens=10000,
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
