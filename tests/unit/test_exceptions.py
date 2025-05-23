"""
Unit tests for custom exception classes.

These tests verify the proper functionality of all custom exception classes
and their error handling capabilities.
"""

from typing import Any, Dict

import pytest

from utils.exceptions import (
    APIError,
    CacheError,
    ClassificationError,
    ClassifierError,
    ConfigurationError,
    ContentExtractionError,
    CSVError,
    FileProcessingError,
    MetadataExtractionError,
    TemplateError,
    ValidationError,
    raise_api_error,
    raise_config_error,
    raise_file_error,
    raise_validation_error,
)


class TestClassifierError:
    """Test the base ClassifierError class."""

    def test_basic_error(self):
        """Test basic error creation and string representation."""
        error = ClassifierError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.details == {}

    def test_error_with_details(self):
        """Test error with additional details."""
        details = {"key1": "value1", "key2": 42}
        error = ClassifierError("Test error", details)

        assert error.message == "Test error"
        assert error.details == details
        assert "key1=value1" in str(error)
        assert "key2=42" in str(error)


class TestConfigurationError:
    """Test ConfigurationError class."""

    def test_basic_config_error(self):
        """Test basic configuration error."""
        error = ConfigurationError("Invalid configuration")
        assert "Invalid configuration" in str(error)
        assert error.config_key is None
        assert error.config_value is None

    def test_config_error_with_key_value(self):
        """Test configuration error with key and value."""
        error = ConfigurationError("Invalid API key", "openai_api_key", "invalid_key")

        assert error.config_key == "openai_api_key"
        assert error.config_value == "invalid_key"
        assert "config_key=openai_api_key" in str(error)
        assert "config_value=invalid_key" in str(error)


class TestFileProcessingError:
    """Test FileProcessingError class."""

    def test_basic_file_error(self):
        """Test basic file processing error."""
        error = FileProcessingError("File not found")
        assert "File not found" in str(error)
        assert error.filepath is None
        assert error.operation is None

    def test_file_error_with_path_operation(self):
        """Test file error with filepath and operation."""
        error = FileProcessingError("Read failed", "/path/to/file.html", "read")

        assert error.filepath == "/path/to/file.html"
        assert error.operation == "read"
        assert "filepath=/path/to/file.html" in str(error)
        assert "operation=read" in str(error)


class TestContentExtractionError:
    """Test ContentExtractionError class."""

    def test_content_extraction_error(self):
        """Test content extraction error."""
        error = ContentExtractionError(
            "Could not extract speaker name", "/path/to/talk.html", "speaker"
        )

        assert error.filepath == "/path/to/talk.html"
        assert error.operation == "content_extraction"
        assert error.content_type == "speaker"
        assert "content_type=speaker" in str(error)


class TestMetadataExtractionError:
    """Test MetadataExtractionError class."""

    def test_metadata_extraction_error(self):
        """Test metadata extraction error."""
        pattern = r"(\d{4})-(\d{2})-(.+)_(.+)\.html"
        error = MetadataExtractionError(
            "Regex pattern did not match", "invalid_filename.html", pattern
        )

        assert error.filepath == "invalid_filename.html"
        assert error.operation == "metadata_extraction"
        assert error.pattern == pattern
        assert "pattern=" in str(error)


class TestAPIError:
    """Test APIError class."""

    def test_basic_api_error(self):
        """Test basic API error."""
        error = APIError("API call failed")
        assert "API call failed" in str(error)
        assert error.api_provider is None
        assert error.status_code is None

    def test_api_error_with_details(self):
        """Test API error with all details."""
        error = APIError(
            "Rate limit exceeded", "OpenAI", 429, "Rate limit exceeded. Please try again later."
        )

        assert error.api_provider == "OpenAI"
        assert error.status_code == 429
        assert "api_provider=OpenAI" in str(error)
        assert "status_code=429" in str(error)
        assert "response_text=Rate limit exceeded" in str(error)

    def test_api_error_long_response_truncation(self):
        """Test that long API responses are truncated."""
        long_response = "Error: " + "x" * 300
        error = APIError("Long response error", response_text=long_response)

        # Should be truncated to 200 chars + "..."
        assert len(error.details["response_text"]) == 203
        assert error.details["response_text"].endswith("...")


class TestClassificationError:
    """Test ClassificationError class."""

    def test_classification_error(self):
        """Test classification error."""
        error = ClassificationError("Model response invalid", "gpt-4", 1500)

        assert error.api_provider == "OpenAI"
        assert error.model == "gpt-4"
        assert error.prompt_length == 1500
        assert "model=gpt-4" in str(error)
        assert "prompt_length=1500" in str(error)


class TestValidationError:
    """Test ValidationError class."""

    def test_validation_error(self):
        """Test validation error."""
        error = ValidationError("Invalid score value", "score", -5, "integer between -3 and 3")

        assert error.field == "score"
        assert error.value == -5
        assert error.expected_type == "integer between -3 and 3"
        assert "field=score" in str(error)
        assert "value=-5" in str(error)
        assert "expected_type=integer between -3 and 3" in str(error)


class TestCSVError:
    """Test CSVError class."""

    def test_csv_error(self):
        """Test CSV error."""
        error = CSVError("Invalid CSV format", "/path/to/data.csv", "read", 42)

        assert error.filepath == "/path/to/data.csv"
        assert error.operation == "read"
        assert error.row_number == 42
        assert "filepath=/path/to/data.csv" in str(error)
        assert "operation=read" in str(error)
        assert "row_number=42" in str(error)


class TestTemplateError:
    """Test TemplateError class."""

    def test_template_error(self):
        """Test template error."""
        error = TemplateError(
            "Template not found", "classify_prompt.jinja", "/templates/classify_prompt.jinja"
        )

        assert error.template_name == "classify_prompt.jinja"
        assert error.template_path == "/templates/classify_prompt.jinja"
        assert "template_name=classify_prompt.jinja" in str(error)
        assert "template_path=/templates/classify_prompt.jinja" in str(error)


class TestCacheError:
    """Test CacheError class."""

    def test_cache_error(self):
        """Test cache error."""
        error = CacheError("Cache miss", "content_hash_123", "get")

        assert error.cache_key == "content_hash_123"
        assert error.operation == "get"
        assert "cache_key=content_hash_123" in str(error)
        assert "operation=get" in str(error)


class TestConvenienceFunctions:
    """Test convenience functions for raising errors."""

    def test_raise_config_error(self):
        """Test raise_config_error convenience function."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise_config_error("Test config error", "test_key", "test_value")

        error = exc_info.value
        assert error.config_key == "test_key"
        assert error.config_value == "test_value"

    def test_raise_file_error(self):
        """Test raise_file_error convenience function."""
        with pytest.raises(FileProcessingError) as exc_info:
            raise_file_error("Test file error", "/test/path", "read")

        error = exc_info.value
        assert error.filepath == "/test/path"
        assert error.operation == "read"

    def test_raise_api_error(self):
        """Test raise_api_error convenience function."""
        with pytest.raises(APIError) as exc_info:
            raise_api_error("Test API error", "TestAPI", 500)

        error = exc_info.value
        assert error.api_provider == "TestAPI"
        assert error.status_code == 500

    def test_raise_validation_error(self):
        """Test raise_validation_error convenience function."""
        with pytest.raises(ValidationError) as exc_info:
            raise_validation_error("Test validation error", "test_field", "invalid_value")

        error = exc_info.value
        assert error.field == "test_field"
        assert error.value == "invalid_value"


class TestErrorInheritance:
    """Test that all custom errors inherit properly from ClassifierError."""

    def test_all_errors_inherit_from_classifier_error(self):
        """Test that all custom exceptions inherit from ClassifierError."""
        errors = [
            ConfigurationError("test"),
            FileProcessingError("test"),
            ContentExtractionError("test"),
            MetadataExtractionError("test"),
            APIError("test"),
            ClassificationError("test"),
            ValidationError("test"),
            CSVError("test"),
            TemplateError("test"),
            CacheError("test"),
        ]

        for error in errors:
            assert isinstance(error, ClassifierError)
            assert isinstance(error, Exception)

    def test_specific_inheritance_hierarchy(self):
        """Test specific inheritance relationships."""
        # ContentExtractionError should inherit from FileProcessingError
        content_error = ContentExtractionError("test")
        assert isinstance(content_error, FileProcessingError)
        assert isinstance(content_error, ClassifierError)

        # MetadataExtractionError should inherit from FileProcessingError
        metadata_error = MetadataExtractionError("test")
        assert isinstance(metadata_error, FileProcessingError)
        assert isinstance(metadata_error, ClassifierError)

        # ClassificationError should inherit from APIError
        classification_error = ClassificationError("test")
        assert isinstance(classification_error, APIError)
        assert isinstance(classification_error, ClassifierError)
