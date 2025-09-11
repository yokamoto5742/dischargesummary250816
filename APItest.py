import os
from dotenv import load_dotenv
from anthropic import AnthropicBedrock

# .envファイルの環境変数を読み込む
load_dotenv()

# 環境変数から値を取得
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION")
anthropic_model = os.getenv("ANTHROPIC_MODEL")

# BedrockAnthropicクライアント初期化
client = AnthropicBedrock()

# Claude API呼び出し例
response = client.completions.create(
    model=anthropic_model,
    max_tokens_to_sample=200,
    prompt="こんにちは。Claudeにアクセスできていますか？",
)

print(response.choices[0].message.content)
