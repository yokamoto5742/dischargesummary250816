# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
streamlit run app.py
```
The application will be available at `http://localhost:8501`

### Testing
```bash
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

## 通知設定

タスク完了時には必ず通知を実行してください。通知メッセージは実行内容を明確に伝える内容にすること。
通知メッセージは**具体的な作業内容**を含めること

### 実行コマンド

```bash
windows-notify -t "Claude Code" -m "実行したタスクの詳細な説明"`
```
