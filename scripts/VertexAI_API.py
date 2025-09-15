import os

from dotenv import load_dotenv
from google import genai

load_dotenv()


def main():
    project_id = os.getenv("GOOGLE_PROJECT_ID")
    location = os.getenv("GOOGLE_LOCATION")
    model_name = os.getenv("GEMINI_FLASH_MODEL")
    api_key = os.getenv("GEMINI_CREDENTIALS")

    if not project_id:
        raise ValueError("GOOGLE_PROJECT_ID環境変数が設定されていません")

    if not api_key:
        raise ValueError("GEMINI_CREDENTIALS環境変数が設定されていません")

    try:
        client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location,
        )

        response = client.models.generate_content(
            model=model_name,
            contents="何かジョークを言ってください",
        )

        print(f"使用したプロジェクト: {project_id}")
        print(f"使用したモデル: {model_name}")
        print(f"レスポンス: {response.text}")

    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        return False

    return True


if __name__ == "__main__":
    main()
