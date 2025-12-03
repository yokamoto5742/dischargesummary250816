# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## House Rules:
- 文章ではなくパッチの差分を返す。
- コードの変更範囲は最小限に抑える。
- コードの修正は直接適用する。
- Pythonのコーディング規約はPEP8に従います。
- KISSの原則に従い、できるだけシンプルなコードにします。
- 可読性を優先します。一度読んだだけで理解できるコードが最高のコードです。
- Pythonのコードのimport文は以下の適切な順序に並べ替えてください。
標準ライブラリ
サードパーティライブラリ
カスタムモジュール 
それぞれアルファベット順に並べます。importが先でfromは後です。

## CHANGELOG
このプロジェクトにおけるすべての重要な変更は日本語でdcos/CHANGELOG.mdに記録します。
フォーマットは[Keep a Changelog](https://keepachangelog.com/ja/1.1.0/)に基づきます。

## Automatic Notifications (Hooks)
自動通知は`.claude/settings.local.json` で設定済：
- **Stop Hook**: ユーザーがClaude Codeを停止した時に「作業が完了しました」と通知
- **SessionEnd Hook**: セッション終了時に「Claude Code セッションが終了しました」と通知

## クリーンコードガイドライン
- 関数のサイズ：関数は50行以下に抑えることを目標にしてください。関数の処理が多すぎる場合は、より小さなヘルパー関数に分割してください。
- 単一責任：各関数とモジュールには明確な目的が1つあるようにします。無関係なロジックをまとめないでください。
- 命名：説明的な名前を使用してください。`tmp` 、`data`、`handleStuff`のような一般的な名前は避けてください。例えば、`doCalc`よりも`calculateInvoiceTotal` の方が適しています。
- DRY原則：コードを重複させないでください。類似のロジックが2箇所に存在する場合は、共有関数にリファクタリングしてください。それぞれに独自の実装が必要な場合はその理由を明確にしてください。
- コメント:分かりにくいロジックについては説明を加えます。説明不要のコードには過剰なコメントはつけないでください。
- コメントとdocstringは必要最小限に日本語で記述します。文末に"。"や"."をつけないでください。

## Development Commands

### Running the Application
```bash
streamlit run app.py
```
The application will be available at `http://localhost:8501`

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run all tests with coverage
python -m pytest tests/ -v --cov=. --cov-report=html

# Run specific test modules
python -m pytest tests/database/ -v
python -m pytest tests/services/ -v 
python -m pytest tests/external_service/ -v

# Run a single test file
python -m pytest tests/services/test_model_service.py -v
```

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables in .env file
# See docs/README.md for required variables
```

#### Automatic Notifications (Hooks)
自動通知はプロジェクトの `.claude/settings.local.json` で設定済みです：

- **Stop Hook**: ユーザーがClaude Codeを停止した時に「作業が完了しました」と通知
- **SessionEnd Hook**: セッション終了時に「Claude Code セッションが終了しました」と通知

## Architecture Overview

This is a Streamlit-based medical document generation application that uses AI APIs (Claude/Gemini) to create discharge summaries and medical histories from medical records.

### Core Architecture Patterns

#### Layered Architecture
- **Views Layer** (`views/`): Streamlit page components and UI logic
- **Services Layer** (`services/`): Business logic and AI model orchestration  
- **Data Layer** (`database/`): PostgreSQL models and repositories using SQLAlchemy
- **External APIs** (`external_service/`): AI API clients with factory pattern

#### Key Design Patterns
- **Factory Pattern**: `external_service/api_factory.py` creates appropriate AI clients
- **Repository Pattern**: `database/repositories.py` abstracts data access
- **Strategy Pattern**: Different AI models (Claude, Gemini) implement `BaseAPIClient`

### Main Data Flow
1. User input → `views/main_page.py`
2. Service orchestration → `services/generation_service.py`
3. AI API selection → `external_service/api_factory.py`
4. Prompt management → `utils/prompt_manager.py`
5. Usage tracking → `database/repositories.py`

### Database Schema
- **prompts**: Custom prompts by department/doctor/document_type
- **summary_usage**: Usage statistics and token tracking
- **app_settings**: User preferences and configurations

### Configuration Management
- Environment variables loaded via `utils/env_loader.py`
- Application constants in `utils/constants.py`
- Department/doctor mappings configurable in constants
- Default prompts in `config.ini`

### AI Model Integration
- **Automatic model switching**: Claude → Gemini when token limits exceeded
- **Token management**: Input validation and usage tracking
- **Error handling**: Comprehensive API error handling and user feedback
- **Prompt hierarchies**: Department → Doctor → Document Type specificity

### Key Features
- Multi-language support (Japanese medical terminology)
- Real-time usage statistics and analytics
- Custom prompt management per department/doctor
- Automatic model fallback for large inputs
- PostgreSQL connection pooling
- Comprehensive test coverage with pytest and mocking

### Testing Strategy
- Unit tests for all services and repositories
- Mock-based testing for external APIs
- Database testing with in-memory SQLite
- Coverage reporting via pytest-cov
