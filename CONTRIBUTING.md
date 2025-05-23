# Contributing to Conference Talk Grace-Works Classifier

Thank you for your interest in contributing to the Conference Talk Grace-Works Classifier! 🎉

This document provides guidelines for contributing to this enterprise-grade, production-ready application. We welcome contributions of all kinds, from bug fixes to new features, documentation improvements, and more.

## 🚀 Quick Start for Contributors

### Prerequisites

- **Python 3.9+** (we test on 3.9, 3.10, 3.11, 3.12)
- **Git** for version control
- **OpenAI API Key** for testing (optional for some contributions)

### Development Setup

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/your-username/conference-talk-classifier.git
   cd conference-talk-classifier
   ```

3. **Set up virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

5. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

6. **Create environment file** (optional):
   ```bash
   cp .env.example .env
   # Add your OpenAI API key if needed for testing
   ```

7. **Verify your setup**:
   ```bash
   pytest
   mypy models.py processors/ utils/
   ```

## 📋 Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Your Changes

Follow our [Code Quality Standards](#-code-quality-standards) while developing.

### 3. Run Quality Checks

```bash
# Format your code
black .
isort .

# Type checking
mypy models.py processors/ utils/

# Run tests
pytest

# Security scanning
bandit -r . --exclude tests
```

### 4. Commit Your Changes

We use conventional commits for clear commit messages:

```bash
git add .
git commit -m "feat: add new classification caching feature"
# or
git commit -m "fix: resolve rate limiting issue in production classifier"
# or
git commit -m "docs: update README with new examples"
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## 🏗️ Code Quality Standards

### Type Safety Requirements

- **100% type hint coverage** for all new code
- **Zero mypy errors** - all code must pass type checking
- Use proper type annotations for function parameters and return values
- Import types from `typing` module when needed

Example:
```python
from typing import List, Optional, Dict, Any
from pathlib import Path

def process_files(files: List[Path], config: Optional[Dict[str, Any]] = None) -> List[str]:
    """Process files and return results."""
    # Implementation here
    pass
```

### Testing Requirements

- **Unit tests** for all new functions and classes
- **Integration tests** for end-to-end workflows
- **Minimum 90% test coverage** for new code
- Tests should use our established patterns in `tests/conftest.py`

Example test structure:
```python
def test_new_feature_success(sample_config):
    """Test that new feature works correctly."""
    # Arrange
    input_data = create_test_data()
    
    # Act
    result = new_feature(input_data, sample_config)
    
    # Assert
    assert result.success
    assert len(result.data) > 0
```

### Code Formatting

We use automated code formatting tools:

- **Black** (line length: 100 characters)
- **isort** for import sorting
- **flake8** for linting

These run automatically via pre-commit hooks, but you can run them manually:

```bash
black .
isort .
flake8 models.py processors/ utils/ tests/ --max-line-length=100
```

### Logging Standards

Use structured logging for all operations:

```python
from utils.logging_config import get_logger, LogContext

logger = get_logger("my_module")

def my_function(data: List[str]) -> None:
    """Example function with proper logging."""
    with LogContext(logger, operation="data_processing", count=len(data)) as log:
        log.info("Starting data processing")
        
        try:
            # Process data
            log.info("Processing completed successfully")
        except Exception as e:
            log.error("Processing failed", error=str(e), error_type=type(e).__name__)
            raise
```

### Documentation Standards

- **Clear docstrings** for all public functions and classes
- **Type information** in docstrings
- **Examples** for complex functions
- **README updates** for new features

Example docstring:
```python
def classify_talk(content: str, metadata: Dict[str, Any]) -> Classification:
    """
    Classify a conference talk on the grace-works spectrum.
    
    Args:
        content: The text content of the talk
        metadata: Talk metadata including speaker, date, etc.
        
    Returns:
        Classification object with score, explanation, and key phrases
        
    Raises:
        ClassificationError: If the API call fails or response is invalid
        
    Example:
        >>> metadata = {"speaker": "John Doe", "year": 2021}
        >>> result = classify_talk("Talk content here...", metadata)
        >>> print(result.score)  # -3 to +3
    """
```

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── unit/                    # Unit tests for individual functions
│   ├── test_models.py
│   ├── test_file_processor.py
│   └── test_exceptions.py
├── integration/             # End-to-end tests
│   └── test_classifier_integration.py
└── conftest.py             # Shared test fixtures
```

### Writing Tests

1. **Use descriptive test names**:
   ```python
   def test_extract_metadata_from_filename_with_speaker_name():
   def test_classification_fails_with_invalid_api_key():
   ```

2. **Follow Arrange-Act-Assert pattern**:
   ```python
   def test_feature():
       # Arrange
       input_data = setup_test_data()
       
       # Act
       result = function_under_test(input_data)
       
       # Assert
       assert result.success
       assert result.data is not None
   ```

3. **Test error conditions**:
   ```python
   def test_function_raises_error_on_invalid_input():
       with pytest.raises(ValidationError):
           function_under_test(invalid_input)
   ```

4. **Use fixtures for common setup**:
   ```python
   @pytest.fixture
   def sample_talk_data():
       return TalkData(
           content="Sample talk content",
           speaker="Test Speaker"
       )
   ```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_models.py

# Specific test
pytest tests/unit/test_models.py::test_classification_creation

# With coverage
pytest --cov=. --cov-report=html

# Performance tests only
pytest -k "benchmark"

# Skip slow tests
pytest -m "not slow"
```

## 🎯 Contribution Areas

### High Priority Areas

1. **Documentation Improvements**
   - API documentation generation
   - Tutorial creation
   - Example workflows
   - Troubleshooting guides

2. **Feature Enhancements**
   - Additional file format support
   - Enhanced caching mechanisms
   - Advanced filtering options
   - Performance optimizations

3. **Testing Expansion**
   - Edge case testing
   - Performance regression tests
   - Load testing
   - Mock service testing

### Medium Priority Areas

1. **UI/UX Improvements**
   - Streamlit dashboard enhancements
   - Data export features
   - Interactive filtering
   - Dark mode support

2. **Infrastructure**
   - Docker containerization
   - Deployment automation
   - Monitoring improvements
   - Logging enhancements

3. **Security Enhancements**
   - Additional security scanning
   - Input validation improvements
   - Authentication mechanisms
   - Rate limiting enhancements

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Clear description** of the issue
2. **Steps to reproduce** the problem
3. **Expected vs. actual behavior**
4. **Environment information**:
   - Python version
   - Operating system
   - Package versions (`pip freeze`)
5. **Log output** (with sensitive information removed)
6. **Sample data** (if applicable and safe to share)

### Bug Report Template

```markdown
## Bug Description
Brief description of the issue

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- Python version: 3.11
- OS: macOS 14.0
- Package versions: (output of `pip freeze`)

## Additional Context
Any other relevant information
```

## 💡 Feature Requests

For feature requests, please include:

1. **Clear description** of the proposed feature
2. **Use case** - why is this needed?
3. **Proposed solution** (if you have ideas)
4. **Alternative solutions** considered
5. **Impact assessment** - who would benefit?

### Feature Request Template

```markdown
## Feature Description
Clear description of the proposed feature

## Use Case
Describe the problem this feature would solve

## Proposed Solution
Your suggested approach

## Alternatives Considered
Other approaches you've thought about

## Additional Context
Any other relevant information
```

## 🔍 Code Review Process

### What We Look For

1. **Functionality**: Does the code work as intended?
2. **Type Safety**: Are all types properly annotated?
3. **Testing**: Are there adequate tests?
4. **Documentation**: Is the code well-documented?
5. **Performance**: Are there any performance concerns?
6. **Security**: Are there any security implications?
7. **Maintainability**: Is the code easy to understand and modify?

### Review Checklist

- [ ] Code follows our formatting standards (Black, isort)
- [ ] All functions have type hints
- [ ] Tests are included and pass
- [ ] Documentation is updated
- [ ] No security vulnerabilities introduced
- [ ] Performance impact considered
- [ ] Backwards compatibility maintained

## 📦 Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

### Release Checklist

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Run full test suite
4. Update documentation
5. Create release notes
6. Tag release in Git

## 🤝 Community Guidelines

### Code of Conduct

- **Be respectful** in all interactions
- **Be inclusive** and welcoming to newcomers
- **Be constructive** in feedback and criticism
- **Be patient** with questions and learning
- **Be professional** in all communications

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Pull Requests**: Code contributions and reviews

## 📚 Additional Resources

### Learning Resources

- [Python Type Hints Guide](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)
- [Structlog Documentation](https://www.structlog.org/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)

### Project Architecture

- **Domain Models**: `models.py` - Core data structures
- **File Processing**: `processors/file_processor.py` - HTML parsing and content extraction
- **Classification**: `processors/classifier_processor.py` - LLM interaction
- **CSV Operations**: `processors/csv_manager.py` - Data persistence and analysis
- **Error Handling**: `utils/exceptions.py` - Custom exception hierarchy
- **Logging**: `utils/logging_config.py` - Structured logging configuration

## 🙏 Thank You

Thank you for contributing to the Conference Talk Grace-Works Classifier! Your contributions help make this tool better for everyone. 

**Questions?** Feel free to open an issue or start a discussion on GitHub.

---

**Happy coding!** 🚀 