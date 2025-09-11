import os
from dotenv import load_dotenv
from anthropic import AnthropicBedrock

load_dotenv()

aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION")
anthropic_model = os.getenv("ANTHROPIC_MODEL")

client = AnthropicBedrock(
    aws_access_key=aws_access_key_id,
    aws_secret_key=aws_secret_access_key,
    aws_region=aws_region,
)

response = client.messages.create(
    model=anthropic_model,
    max_tokens=200,
    messages=[
        {
            "role": "user",
            "content": "こんにちは。Claudeにアクセスできていますか？"
        }
    ]
)

print(response.content[0].text)
