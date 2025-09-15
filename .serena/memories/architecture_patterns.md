# Architecture Patterns

## Layered Architecture
- **Views Layer** (`views/`): Streamlit page components and UI logic
- **Services Layer** (`services/`): Business logic and AI model orchestration  
- **Data Layer** (`database/`): PostgreSQL models and repositories using SQLAlchemy
- **External APIs** (`external_service/`): AI API clients with factory pattern

## Key Design Patterns
- **Factory Pattern**: `external_service/api_factory.py` creates appropriate AI clients
- **Repository Pattern**: `database/repositories.py` abstracts data access
- **Strategy Pattern**: Different AI models (Claude, Gemini) implement `BaseAPIClient`
- **Abstract Base Class**: `BaseAPIClient` defines interface for AI clients

## Configuration Management
- Environment variables loaded via `utils/env_loader.py`
- Application constants in `utils/constants.py`
- Error messages centralized in `utils/constants.py.MESSAGES`
- Department/doctor mappings configurable in constants

## Database Schema
- **prompts**: Custom prompts by department/doctor/document_type
- **summary_usage**: Usage statistics and token tracking
- **app_settings**: User preferences and configurations