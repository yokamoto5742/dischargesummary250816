# Medical Document Generation Application

## Project Purpose
This is a Streamlit-based medical document generation application that uses AI APIs (Claude/Gemini) to create discharge summaries (退院時サマリ) and medical histories (現病歴) from medical records. The application is designed for Japanese medical professionals.

## Tech Stack
- **Frontend**: Streamlit (Japanese UI)
- **Database**: PostgreSQL with SQLAlchemy
- **AI APIs**: Claude (Anthropic/Bedrock), Gemini (Google AI)
- **Authentication**: Environment variable based
- **Testing**: pytest with coverage and mocking
- **Deployment**: Configurable via environment variables

## Key Features
- Multi-language support (Japanese medical terminology)  
- Real-time usage statistics and analytics
- Custom prompt management per department/doctor
- Automatic model fallback (Claude → Gemini) for large inputs
- Token usage tracking and management
- PostgreSQL connection pooling

## Main Entry Point
- `streamlit run app.py` - starts the application at http://localhost:8501