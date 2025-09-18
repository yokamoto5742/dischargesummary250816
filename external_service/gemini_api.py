import json
import os
from typing import Tuple

from google import genai
from google.genai import types
from google.oauth2 import service_account

from external_service.base_api import BaseAPIClient
from utils.config import GEMINI_MODEL, GEMINI_THINKING_BUDGET, GOOGLE_PROJECT_ID, GOOGLE_LOCATION
from utils.constants import MESSAGES
from utils.exceptions import APIError


class GeminiAPIClient(BaseAPIClient):
    def __init__(self):
        super().__init__(None, GEMINI_MODEL)
        self.client = None

    def initialize(self) -> bool:
        try:
            if not GOOGLE_PROJECT_ID:
                raise APIError(MESSAGES["VERTEX_AI_PROJECT_MISSING"])

            google_credentials_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
            
            if google_credentials_json:
                try:
                    credentials_dict = json.loads(google_credentials_json)

                    credentials = service_account.Credentials.from_service_account_info(
                        credentials_dict,
                        scopes=['https://www.googleapis.com/auth/cloud-platform']
                    )

                    self.client = genai.Client(
                        vertexai=True,
                        project=GOOGLE_PROJECT_ID,
                        location=GOOGLE_LOCATION,
                        credentials=credentials
                    )
                    
                    print(f"Vertex AI Client initialized successfully for project: {GOOGLE_PROJECT_ID}")
                    
                except json.JSONDecodeError as e:
                    raise APIError(f"GOOGLE_CREDENTIALS_JSON環境変数の解析エラー: {str(e)}")
                except KeyError as e:
                    raise APIError(f"認証情報に必要なフィールドが不足: {str(e)}")
                except Exception as e:
                    raise APIError(f"認証情報の作成エラー: {str(e)}")
            else:
                self.client = genai.Client(
                    vertexai=True,
                    project=GOOGLE_PROJECT_ID,
                    location=GOOGLE_LOCATION,
                )
            
            return True
        except APIError:
            raise
        except Exception as e:
            raise APIError(MESSAGES["VERTEX_AI_INIT_ERROR"].format(error=str(e)))

    def _generate_content(self, prompt: str, model_name: str) -> Tuple[str, int, int]:
        try:
            if GEMINI_THINKING_BUDGET:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(
                            thinking_budget=GEMINI_THINKING_BUDGET
                        )
                    )
                )
            else:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )

            if hasattr(response, 'text'):
                summary_text = response.text
            else:
                summary_text = str(response)

            input_tokens = 0
            output_tokens = 0

            if hasattr(response, 'usage_metadata'):
                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count

            return summary_text, input_tokens, output_tokens
        except Exception as e:
            raise APIError(MESSAGES["VERTEX_AI_API_ERROR"].format(error=str(e)))
