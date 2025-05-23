# API Reference

This document provides comprehensive API documentation for the Conference Talk Grace-Works Classifier.

## 📋 Table of Contents

1. [Domain Models](#-domain-models)
2. [Processors](#-processors)
3. [Utilities](#-utilities)
4. [Configuration](#-configuration)
5. [Examples](#-examples)

## 🏗️ Domain Models

### `models.py`

#### `TalkMetadata`

```python
@dataclass
class TalkMetadata:
    """Metadata extracted from conference talk files."""
    
    year: int
    month: int
    conference_session_id: str
    talk_identifier: str
    speaker_name_from_filename: Optional[str] = None
```

**Attributes:**
- `year`: Conference year (e.g., 2021)
- `month`: Conference month (typically 4 or 10)
- `conference_session_id`: Session identifier from filename
- `talk_identifier`: Unique talk identifier
- `speaker_name_from_filename`: Speaker name extracted from filename

#### `Classification`

```python
@dataclass
class Classification:
    """Classification result for a conference talk."""
    
    score: int  # -3 to +3
    explanation: str
    key_phrases: List[str]
    model_used: str = "gpt-4"
```

**Attributes:**
- `score`: Grace-works score (-3=strong grace, +3=strong works)
- `explanation`: Detailed explanation of the classification
- `key_phrases`: Important phrases that influenced the classification
- `model_used`: OpenAI model used for classification

#### `ProcessingResult[T]`

```python
@dataclass
class ProcessingResult(Generic[T]):
    """Generic result container for processing operations."""
    
    success: bool
    data: Optional[T]
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
```

**Type Parameters:**
- `T`: The type of data returned on success

**Attributes:**
- `success`: Whether the operation succeeded
- `data`: The result data (if successful)
- `error_message`: Human-readable error message
- `error_type`: Error type for programmatic handling
- `context`: Additional context information

#### `ClassifierConfig`

```python
@dataclass
class ClassifierConfig:
    """Configuration for the classifier application."""
    
    openai_api_key: str
    openai_model: str = "gpt-4"
    input_dir: Path = Path("conference_talks")
    output_dir: Path = Path("output")
    templates_dir: Path = Path("templates")
    rate_limit_seconds: float = 0.1
    batch_size: int = 50
```

**Attributes:**
- `openai_api_key`: OpenAI API key
- `openai_model`: Model to use for classification
- `input_dir`: Directory containing talk files
- `output_dir`: Directory for output files
- `templates_dir`: Directory containing prompt templates
- `rate_limit_seconds`: Delay between API calls
- `batch_size`: Batch size for incremental saving

## 🔧 Processors

### `processors.file_processor`

#### `extract_metadata_from_filename(filename: str) -> ProcessingResult[TalkMetadata]`

Extracts metadata from conference talk filename.

**Parameters:**
- `filename`: The filename to parse

**Returns:**
- `ProcessingResult[TalkMetadata]`: Metadata extraction result

**Example:**
```python
result = extract_metadata_from_filename("2021-04-general-conference-example-talk_john-doe.html")
if result.success:
    metadata = result.data
    print(f"Year: {metadata.year}, Speaker: {metadata.speaker_name_from_filename}")
```

#### `extract_body_text_and_speaker(file_path: Path) -> ProcessingResult[Tuple[str, Optional[str]]]`

Extracts text content and speaker name from HTML file.

**Parameters:**
- `file_path`: Path to the HTML file

**Returns:**
- `ProcessingResult[Tuple[str, Optional[str]]]`: Content and speaker extraction result

### `processors.classifier_processor`

#### `get_llm_classification(content: str, metadata: TalkMetadata, config: ClassifierConfig) -> ProcessingResult[Classification]`

Classifies talk content using OpenAI's language model.

**Parameters:**
- `content`: The talk text content
- `metadata`: Talk metadata
- `config`: Classifier configuration

**Returns:**
- `ProcessingResult[Classification]`: Classification result

### `processors.csv_manager`

#### `write_to_csv(results: List[Tuple[TalkMetadata, str, Classification]], output_path: Path) -> ProcessingResult[None]`

Writes classification results to CSV file.

**Parameters:**
- `results`: List of (metadata, content, classification) tuples
- `output_path`: Path for the output CSV file

**Returns:**
- `ProcessingResult[None]`: Write operation result

#### `load_processed_talks_from_csv(csv_path: Path) -> ProcessingResult[Set[str]]`

Loads previously processed talk filenames from CSV.

**Parameters:**
- `csv_path`: Path to the CSV file

**Returns:**
- `ProcessingResult[Set[str]]`: Set of processed filenames

## 🛠️ Utilities

### `utils.exceptions`

#### Custom Exception Hierarchy

```python
class ClassifierError(Exception):
    """Base exception for classifier errors."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context or {}
```

**Specialized Exceptions:**
- `ConfigurationError`: Configuration-related errors
- `FileProcessingError`: File processing errors
- `ContentExtractionError`: Content extraction errors
- `MetadataExtractionError`: Metadata extraction errors
- `APIError`: OpenAI API errors
- `ClassificationError`: Classification logic errors
- `ValidationError`: Data validation errors
- `CSVError`: CSV operation errors
- `TemplateError`: Template processing errors
- `CacheError`: Caching operation errors

#### Convenience Functions

```python
def api_error(message: str, status_code: Optional[int] = None, response: Optional[str] = None) -> APIError
def file_error(message: str, file_path: Optional[Path] = None, operation: Optional[str] = None) -> FileProcessingError
def validation_error(message: str, field: Optional[str] = None, value: Optional[Any] = None) -> ValidationError
```

### `utils.logging_config`

#### `setup_logging(level: str, log_file: Optional[Path], json_format: bool, include_console: bool, context: Optional[Dict[str, Any]]) -> logging.Logger`

Sets up structured logging configuration.

**Parameters:**
- `level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `log_file`: Optional file path for log output
- `json_format`: Whether to use JSON formatting
- `include_console`: Whether to include console output
- `context`: Additional context for all log messages

#### `get_logger(name: str = "classifier") -> structlog.stdlib.BoundLogger`

Gets a structured logger instance.

#### `LogContext`

Context manager for adding temporary logging context.

```python
with LogContext(logger, operation="processing", file_count=100) as log:
    log.info("Starting processing")
    # Processing happens here
    log.info("Processing completed")
```

#### `log_performance(logger: structlog.stdlib.BoundLogger, operation: str) -> Callable[[F], F]`

Decorator for logging performance metrics.

```python
@log_performance(logger, "file_processing")
def process_file(file_path: Path) -> ProcessingResult[str]:
    # Function implementation
    pass
```

## ⚙️ Configuration

### Environment Variables

The application supports the following environment variables:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OPENAI_API_KEY` | str | **Required** | OpenAI API key |
| `OPENAI_MODEL` | str | "gpt-4" | Model for classification |
| `LOG_LEVEL` | str | "INFO" | Logging level |
| `ENVIRONMENT` | str | "development" | Application environment |
| `RATE_LIMIT_SECONDS` | float | 0.1 | Rate limiting delay |

### Configuration Loading

```python
from models import ClassifierConfig

# Load from environment variables
config = ClassifierConfig.from_env()

# Load with custom values
config = ClassifierConfig(
    openai_api_key="your-api-key",
    openai_model="gpt-4-turbo",
    rate_limit_seconds=0.5
)
```

## 📚 Examples

### Basic Classification

```python
from pathlib import Path
from models import ClassifierConfig
from processors.file_processor import extract_metadata_from_filename, extract_body_text_and_speaker
from processors.classifier_processor import get_llm_classification

# Setup configuration
config = ClassifierConfig.from_env()

# Process a single file
file_path = Path("conference_talks/2021-04-example.html")

# Extract metadata
metadata_result = extract_metadata_from_filename(file_path.name)
if not metadata_result.success:
    print(f"Metadata extraction failed: {metadata_result.error_message}")
    exit(1)

metadata = metadata_result.data

# Extract content
content_result = extract_body_text_and_speaker(file_path)
if not content_result.success:
    print(f"Content extraction failed: {content_result.error_message}")
    exit(1)

content, speaker = content_result.data

# Classify
classification_result = get_llm_classification(content, metadata, config)
if classification_result.success:
    classification = classification_result.data
    print(f"Score: {classification.score}")
    print(f"Explanation: {classification.explanation}")
else:
    print(f"Classification failed: {classification_result.error_message}")
```

### Batch Processing

```python
from pathlib import Path
from typing import List, Tuple
from models import ClassifierConfig, TalkMetadata, Classification
from processors.csv_manager import write_to_csv

def process_talks(file_paths: List[Path], config: ClassifierConfig) -> List[Tuple[TalkMetadata, str, Classification]]:
    """Process multiple talks and return results."""
    results = []
    
    for file_path in file_paths:
        # Extract metadata
        metadata_result = extract_metadata_from_filename(file_path.name)
        if not metadata_result.success:
            continue
            
        # Extract content
        content_result = extract_body_text_and_speaker(file_path)
        if not content_result.success:
            continue
            
        # Classify
        classification_result = get_llm_classification(
            content_result.data[0], 
            metadata_result.data, 
            config
        )
        if classification_result.success:
            results.append((
                metadata_result.data,
                content_result.data[0],
                classification_result.data
            ))
    
    return results

# Usage
config = ClassifierConfig.from_env()
file_paths = list(Path("conference_talks").glob("*.html"))
results = process_talks(file_paths, config)

# Save results
output_path = Path("output/results.csv")
write_result = write_to_csv(results, output_path)
if write_result.success:
    print(f"Results saved to {output_path}")
```

### Custom Logging

```python
from utils.logging_config import setup_logging, get_logger, LogContext

# Setup logging
setup_logging(
    level="INFO",
    log_file=Path("logs/classifier.log"),
    json_format=True,
    include_console=True,
    context={"application": "classifier", "version": "1.0.0"}
)

logger = get_logger("my_module")

# Use contextual logging
with LogContext(logger, operation="batch_processing", batch_size=100) as log:
    log.info("Starting batch processing")
    
    try:
        # Processing logic here
        log.info("Batch processing completed successfully")
    except Exception as e:
        log.error("Batch processing failed", error=str(e), error_type=type(e).__name__)
        raise
```

### Error Handling

```python
from utils.exceptions import api_error, file_error, ClassificationError

# Raise specific errors
try:
    # API call
    response = call_openai_api(content)
except Exception as e:
    raise api_error(
        "OpenAI API call failed",
        status_code=500,
        response=str(e)
    )

# Handle errors with context
try:
    result = process_file(file_path)
except FileProcessingError as e:
    print(f"File processing failed: {e}")
    print(f"Context: {e.context}")
```

## 🔍 Type Checking

All modules are fully type-hinted and compatible with mypy:

```bash
# Check types
mypy models.py processors/ utils/

# Check specific module
mypy processors/file_processor.py
```

## 🧪 Testing

The API includes comprehensive test fixtures:

```python
import pytest
from tests.conftest import sample_config, sample_metadata, sample_classification

def test_classification_creation(sample_classification):
    """Test classification object creation."""
    assert sample_classification.score in range(-3, 4)
    assert len(sample_classification.explanation) > 0
    assert len(sample_classification.key_phrases) > 0
```

---

**For more examples and usage patterns, see our [User Guide](USER_GUIDE.md) and [Contributing Guidelines](../CONTRIBUTING.md).** 