import os
from dotenv import load_dotenv
from anthropic import AnthropicBedrock  # AnthropicBedrock はそのまま使用

# .envファイルの環境変数を読み込む
load_dotenv()

# 環境変数から値を取得
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION")
anthropic_model = os.getenv("ANTHROPIC_MODEL")

# BedrockAnthropicクライアント初期化
client = AnthropicBedrock(
    aws_access_key=aws_access_key_id,
    aws_secret_key=aws_secret_access_key,
    aws_region=aws_region,
)

# 【修正箇所】completions.create から messages.create へ変更
response = client.messages.create(
    model=anthropic_model,
    max_tokens=200,  # パラメータ名が max_tokens_to_sample から max_tokens に変更
    messages=[
        {
            "role": "user",
            "content": "こんにちは。Claudeにアクセスできていますか？"
        }
    ]
)

# 応答の取得方法も変更
print(response.content[0].text)