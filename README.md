# Conference Talk Grace-Works Classifier

[![CI/CD Pipeline](https://github.com/example/conference-talk-classifier/actions/workflows/ci.yml/badge.svg)](https://github.com/example/conference-talk-classifier/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/example/conference-talk-classifier/branch/main/graph/badge.svg)](https://codecov.io/gh/example/conference-talk-classifier)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

> **A production-ready, type-safe, and enterprise-grade classifier for analyzing conference talks on a grace-works theological spectrum using OpenAI's API.**

## 🌟 Features

### Core Functionality
- **🧠 Intelligent Classification**: Uses OpenAI's language models to analyze conference talks and classify them on a Grace-Works theological spectrum (-3 to +3)
- **📊 Data Visualization**: Interactive Streamlit dashboard with time-series analysis, speaker insights, and score distributions
- **⚡ Performance Optimized**: Includes caching, rate limiting, progress tracking, and batch processing capabilities
- **🔄 Resume Support**: Intelligent resumption from previous processing sessions

### Enterprise Features
- **🛡️ Type Safety**: 100% type hint coverage with mypy validation
- **📝 Structured Logging**: Comprehensive logging with JSON output and contextual information
- **🧪 Comprehensive Testing**: 69+ unit and integration tests with full coverage
- **🔒 Security Scanning**: Automated security analysis and dependency auditing
- **🎨 Code Quality**: Automated formatting with Black, import sorting with isort
- **⚙️ CI/CD Pipeline**: GitHub Actions with automated testing, security, and quality checks

### Multiple Interfaces
- **Production Classifier**: `classifier_production.py` with structured logging and enhanced error handling
- **Optimized Classifier**: `classifier_optimized.py` with progress tracking and caching
- **Batch Processing**: Generate JSONL files for OpenAI's batch API
- **Interactive Dashboard**: Streamlit web application for data exploration

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+** (tested on 3.9, 3.10, 3.11, 3.12)
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
- **Conference talk files** in HTML format

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/example/conference-talk-classifier.git
   cd conference-talk-classifier
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

### Basic Usage

#### 1. Process Conference Talks (Production)

```bash
# Process all talks with structured logging
python classifier_production.py

# Process specific number of talks with debug logging
python classifier_production.py --num-talks 10 --log-level DEBUG

# Process with JSON logging for production monitoring
python classifier_production.py --log-json --no-progress

# Resume from previous session
python classifier_production.py --resume-from-csv output/previous_results.csv
```

#### 2. Launch Interactive Dashboard

```bash
streamlit run streamlit_app_typed.py
```

#### 3. Generate Batch Processing File

```bash
python classifier_production.py --generate-batch-input batch_requests.jsonl --num-talks 50
```

## 📊 Sample Output

### Classification Results
```csv
filename,year,month,conference_session_id,talk_identifier,speaker_name,text_preview,score,explanation,key_phrases,model_used
2021-04-01_example-talk_john-doe.html,2021,4,general-conference,example-talk,John Doe,"In this inspiring message...",2,"This talk emphasizes grace through Christ's atonement...","grace, redemption, faith",gpt-4
```

### Structured Logging
```json
{
  "timestamp": "2025-05-23T01:49:07.097599",
  "level": "INFO", 
  "operation": "main_execution",
  "event": "Starting Conference Talk Grace-Works Classifier",
  "file_count": 4182,
  "model": "gpt-4",
  "application": "conference-talk-classifier",
  "version": "1.0.0"
}
```

## 🏗️ Architecture

### Project Structure
```
conference-talk-classifier/
├── 📁 processors/           # Core processing modules
│   ├── file_processor.py    # File parsing and content extraction
│   ├── classifier_processor.py  # LLM classification logic
│   └── csv_manager.py       # CSV operations and analysis
├── 📁 utils/               # Utility modules
│   ├── exceptions.py        # Custom exception hierarchy
│   └── logging_config.py    # Structured logging configuration
├── 📁 tests/               # Comprehensive test suite
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── 📁 templates/           # Jinja2 templates for prompts
├── 📁 docs/                # Comprehensive documentation
│   ├── USER_GUIDE.md       # Complete user guide
│   └── API_REFERENCE.md    # API documentation
├── 📁 archive/             # Archived legacy files (see archive/README.md)
├── 📄 models.py            # Type-safe domain models
├── 📄 classifier_production.py  # Production classifier
├── 📄 classifier_optimized.py   # Performance-optimized classifier
├── 📄 streamlit_app_typed.py    # Interactive dashboard
└── 📄 pyproject.toml       # Project configuration
```

> **Note**: This project maintains a clean, professional structure. Legacy files and development artifacts have been organized in the `archive/` directory. See `archive/README.md` for details about the project's evolution from prototype to enterprise-grade application.

### Domain Models

**Type-safe dataclasses** for all data structures:

```python
@dataclass
class Classification:
    score: int  # -3 to +3 (Works ← → Grace)
    explanation: str
    key_phrases: List[str]

@dataclass 
class TalkMetadata:
    year: int
    month: int
    conference_session_id: str
    talk_identifier: str
    speaker_name_from_filename: Optional[str]
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with:

```bash
# Required
OPENAI_API_KEY=your_api_key_here

# Optional
OPENAI_MODEL=gpt-4                    # Default: gpt-4
LOG_LEVEL=INFO                        # DEBUG, INFO, WARNING, ERROR, CRITICAL
ENVIRONMENT=production                # development, staging, production
```

### CLI Options

#### Production Classifier Options
```bash
python classifier_production.py [OPTIONS]

Options:
  --num-talks INT           Number of talks to process
  --file PATH              Process single file
  --resume-from-csv PATH   Resume from previous results
  --model TEXT             OpenAI model to use
  --rate-limit FLOAT       Seconds between API calls (default: 0.1)
  --log-level LEVEL        Logging level
  --log-json               Output JSON logs
  --no-progress           Disable progress bars
```

## 🧪 Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test types
pytest tests/unit/           # Unit tests only
pytest tests/integration/    # Integration tests only
pytest -m "not slow"        # Skip slow tests
```

### Code Quality

```bash
# Format code
black .
isort .

# Type checking
mypy models.py processors/ utils/

# Security scanning
bandit -r . --exclude tests
safety check

# Pre-commit hooks (automatically run on commit)
pre-commit install
```

### Performance Benchmarking

```bash
pytest tests/ -k "benchmark" --benchmark-only
```

## 📈 Performance & Costs

### Processing Performance

| File Count | Processing Time* | Est. Cost** |
|------------|------------------|-------------|
| 10 talks   | ~2 minutes       | $0.15       |
| 100 talks  | ~15 minutes      | $1.50       |
| 1000 talks | ~2.5 hours       | $15.00      |

*With rate limiting (0.1s between calls)  
**Estimates using GPT-4 at current rates ($2.00/1M input + $8.00/1M output tokens)

### Optimization Features

- **Classification Caching**: Avoids re-processing duplicate content
- **Rate Limiting**: Configurable delays to respect API limits
- **Progress Tracking**: Visual progress bars with ETA
- **Incremental Saving**: Results saved in batches to prevent data loss
- **Resume Capability**: Continue from previous sessions

## 📊 Dashboard Features

### Interactive Visualizations

1. **Time Series Analysis**: Score trends over time
2. **Speaker Analysis**: Individual speaker score distributions  
3. **Conference Patterns**: Scoring patterns by conference session
4. **Score Distribution**: Overall grace-works balance analysis

### Data Filters

- Date range selection
- Conference session filtering
- Speaker-specific analysis
- Score range filtering

## 🔒 Security

### Implemented Security Measures

- **API Key Protection**: Environment variable storage
- **Input Validation**: Comprehensive data validation
- **Security Scanning**: Automated vulnerability detection
- **Dependency Auditing**: Regular dependency security checks
- **Type Safety**: Prevention of runtime type errors

### Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive configuration
3. **Regularly update dependencies** to patch vulnerabilities
4. **Review security scan results** in CI/CD pipeline

## 🚨 Troubleshooting

### Common Issues

#### 1. OpenAI API Errors

**Rate Limit Exceeded**
```bash
# Increase rate limiting delay
python classifier_production.py --rate-limit 1.0
```

**Invalid API Key**
```bash
# Verify your .env file
echo $OPENAI_API_KEY
```

#### 2. File Processing Issues

**No Files Found**
```bash
# Check directory structure
ls conference_talks/
```

**Permission Errors**
```bash
# Ensure read permissions
chmod -R 755 conference_talks/
```

#### 3. Memory Issues

**Large File Processing**
```bash
# Process in smaller batches
python classifier_production.py --num-talks 50
```

### Debugging

Enable debug logging for detailed information:

```bash
python classifier_production.py --log-level DEBUG
```

Check log files:
```bash
tail -f logs/classifier_$(date +%Y%m%d).log
```

## 🤝 Contributing

### Development Setup

1. **Fork and clone** the repository
2. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```
3. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```
4. **Run tests** to ensure everything works:
   ```bash
   pytest
   ```

### Code Quality Standards

- **100% type hint coverage** for all new code
- **Comprehensive testing** for new features
- **Structured logging** for all operations
- **Clear documentation** for APIs and functions

### Pull Request Process

1. Create feature branch from `main`
2. Implement changes with tests
3. Ensure all quality checks pass
4. Update documentation as needed
5. Submit pull request with clear description

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Acknowledgments

- **OpenAI** for providing the language model API
- **Streamlit** for the interactive dashboard framework
- **Python Community** for excellent development tools and libraries

## 📬 Support

- **Issues**: [GitHub Issues](https://github.com/example/conference-talk-classifier/issues)
- **Discussions**: [GitHub Discussions](https://github.com/example/conference-talk-classifier/discussions)
- **Documentation**: [Full Documentation](https://conference-talk-classifier.readthedocs.io/)

---

**Built with ❤️ and enterprise-grade engineering practices** 