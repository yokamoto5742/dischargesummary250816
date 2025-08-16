from anthropic import Anthropic
from typing import Tuple

from external_service.base_api import BaseAPIClient
from utils.config import CLAUDE_API_KEY, CLAUDE_MODEL
from utils.constants import MESSAGES
from utils.exceptions import APIError


class ClaudeAPIClient(BaseAPIClient):
    def __init__(self):
        super().__init__(CLAUDE_API_KEY, CLAUDE_MODEL)
        self.client = None

    def initialize(self) -> bool:
        try:
            if self.api_key:
                self.client = Anthropic(api_key=self.api_key)
                return True
            else:
                raise APIError(MESSAGES["API_CREDENTIALS_MISSING"])
        except Exception as e:
            raise APIError(f"Claude API初期化エラー: {str(e)}")

    def _generate_content(self, prompt: str, model_name: str) -> Tuple[str, int, int]:
        response = self.client.messages.create(
            model=model_name,
            max_tokens=6000, # 最大出力トークン数
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
