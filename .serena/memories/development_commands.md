# Development Commands

## Running the Application
```bash
streamlit run app.py
```
Application available at http://localhost:8501

## Testing Commands  
```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage  
python -m pytest tests/ -v --cov=. --cov-report=html

# Run specific modules
python -m pytest tests/database/ -v
python -m pytest tests/services/ -v
python -m pytest tests/external_service/ -v
```

## Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Environment variables in .env file required
```

## Code Style Conventions
- Python import order: standard lib → third party → custom modules (alphabetical)
- Error messages managed in `utils/constants.py.MESSAGES`
- Japanese UI text and medical terminology
- Type hints used throughout
- Abstract base classes for interfaces