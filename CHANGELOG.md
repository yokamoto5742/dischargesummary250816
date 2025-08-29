# Changelog

All notable changes to the MediDocsLMsummary project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive project analysis and documentation understanding
- Structured architecture overview with layered design patterns
- Database schema analysis with 3-table structure (prompts, summary_usage, app_settings)
- AI service integration analysis (Claude + Gemini APIs with automatic fallback)
- Code quality assessment and security review completed
- Desktop notification system for task completion in CLAUDE.md
- Automatic notification hooks system (.claude/settings.local.json)
- Manual and automatic notification commands in development workflow

### Changed
- Updated CLAUDE.md with notification system requirements
- Enhanced development guidelines with specific notification commands
- Added hooks configuration for Stop and SessionEnd events
- Expanded notification section with manual vs automatic options

### Fixed
- Fixed datetime mocking issue in summary service tests (tests/services/test_summary_service.py:243)
- Fixed text processor inline content parsing issue with colon removal (utils/text_processor.py)
- All unit tests now pass (248 tests, 2 previously failing tests resolved)

## [Recent Updates] - 2025-01-28

### Added
- ✨ feat(ドキュメント): CLAUDE.mdの新規作成と開発ガイドラインの追加 (f8cb005)
- 📝 feat(docs/README.md): 退院時サマリ作成機能とモデル切替の説明を更新 (96c40e9)
- ✨ feat(utils/constants): MODEL_OPTIONS 定数を定義し、モデル選択肢を拡張 (1f90759)

### Fixed
- ✨ refactor(database/models.py): ORMインポートを修正し、declarative_baseを正しくインポート (c39d53b)
- 🎯 test: 修正済みのドキュメントタイプを退院時サマリに更新 (ea471e5)
- 🧪 テストケースの日本語エラーメッセージ統一とカバレッジ向上 (71b8dea)

### Changed
- 🔧 refactor(ui_components/navigation.py): 注意喚起の文言を簡潔に改良 (0cfaf18)
- 📝 refactor(views/statistics_page): モデル選択肢をMODEL_OPTIONSに統一 (1f90759)
- ✨ feat(utils/text_processor.py): セクションエイリアスを英語に統一 (f55569a)

## Project Structure Analysis

### Architecture Components Analyzed
- **Frontend**: Streamlit-based UI with Japanese medical terminology support
- **Backend**: PostgreSQL with SQLAlchemy ORM
- **AI Integration**: Dual API support (Claude + Gemini) with automatic switching
- **Testing**: Comprehensive pytest suite with mocking and coverage reporting

### Security Assessment
- ✅ No malicious code detected in analyzed files
- ✅ Proper API credential handling through environment variables  
- ✅ Input validation and error handling implemented
- ✅ Database operations use ORM protection against SQL injection

### Code Quality Findings
- Well-structured layered architecture
- Consistent Japanese documentation and comments
- Comprehensive test coverage with mocking
- Proper separation of concerns across modules
- Factory and Repository patterns implemented correctly