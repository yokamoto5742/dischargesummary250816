import configparser
import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()


def get_config():
    config = configparser.ConfigParser()
    base_dir = Path(__file__).parent.parent
    config_path = os.path.join(base_dir, 'config.ini')
    config.read(config_path, encoding='utf-8')
    return config


def parse_database_url():
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        parsed = urlparse(database_url)
        return {
            "host": parsed.hostname,
            "port": parsed.port,
            "user": parsed.username,
            "password": parsed.password,
            "database": parsed.path[1:]
        }
    return None


db_config = parse_database_url()

POSTGRES_HOST = db_config["host"]
POSTGRES_PORT = db_config["port"]
POSTGRES_USER = db_config["user"]
POSTGRES_PASSWORD = db_config["password"]
POSTGRES_DB = db_config["database"]
POSTGRES_SSL = "require"

DB_POOL_SIZE = int(os.environ.get("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.environ.get("DB_MAX_OVERFLOW", "10"))
DB_POOL_TIMEOUT = int(os.environ.get("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.environ.get("DB_POOL_RECYCLE", "3600"))

GEMINI_CREDENTIALS = os.environ.get("GEMINI_CREDENTIALS")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL")
GEMINI_FLASH_MODEL = os.environ.get("GEMINI_FLASH_MODEL")
GEMINI_THINKING_BUDGET = int(os.environ.get("GEMINI_THINKING_BUDGET")) if os.environ.get("GEMINI_THINKING_BUDGET") else None

# AWS Bedrock認証情報
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL")

# Claude API設定（従来のAPIキーまたはBedrock経由）
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", ANTHROPIC_MODEL)

# Bedrock経由でClaudeが利用可能かチェック
CLAUDE_BEDROCK_AVAILABLE = all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, ANTHROPIC_MODEL])

# ClaudeがAPI KeyまたはBedrock経由で利用可能かチェック
CLAUDE_AVAILABLE = CLAUDE_API_KEY or CLAUDE_BEDROCK_AVAILABLE

SELECTED_AI_MODEL = os.environ.get("SELECTED_AI_MODEL", "claude")
MAX_INPUT_TOKENS = int(os.environ.get("MAX_INPUT_TOKENS", "300000"))
MIN_INPUT_TOKENS = int(os.environ.get("MIN_INPUT_TOKENS", "100"))
MAX_TOKEN_THRESHOLD = int(os.environ.get("MAX_TOKEN_THRESHOLD", "100000"))

APP_TYPE = os.environ.get("APP_TYPE", "dischargesummary")
PROMPT_MANAGEMENT = os.environ.get("PROMPT_MANAGEMENT", "True").lower() == "true"