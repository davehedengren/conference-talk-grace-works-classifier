"""
Custom exception classes for the Conference Talk Grace-Works Classifier.

This module provides a hierarchy of specific exceptions to improve error handling
and debugging throughout the application.
"""

from typing import Any, Dict, Optional


class ClassifierError(Exception):
    """Base exception class for all classifier-related errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the base classifier error.

        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} (Details: {detail_str})"
        return self.message


class ConfigurationError(ClassifierError):
    """Raised when there are configuration-related errors."""

    def __init__(
        self, message: str, config_key: Optional[str] = None, config_value: Optional[Any] = None
    ):
        """
        Initialize configuration error.

        Args:
            message: Error message
            config_key: The configuration key that caused the error
            config_value: The problematic configuration value
        """
        details: Dict[str, Any] = {}
        if config_key:
            details["config_key"] = config_key
        if config_value is not None:
            details["config_value"] = config_value

        super().__init__(message, details)
        self.config_key: Optional[str] = config_key
        self.config_value: Optional[Any] = config_value


class FileProcessingError(ClassifierError):
    """Raised when file processing operations fail."""

    def __init__(
        self, message: str, filepath: Optional[str] = None, operation: Optional[str] = None
    ):
        """
        Initialize file processing error.

        Args:
            message: Error message
            filepath: Path to the file that caused the error
            operation: The operation that failed (e.g., 'read', 'parse', 'extract')
        """
        details: Dict[str, Any] = {}
        if filepath:
            details["filepath"] = filepath
        if operation:
            details["operation"] = operation

        super().__init__(message, details)
        self.filepath: Optional[str] = filepath
        self.operation: Optional[str] = operation


class ContentExtractionError(FileProcessingError):
    """Raised when content extraction from HTML files fails."""

    def __init__(
        self, message: str, filepath: Optional[str] = None, content_type: Optional[str] = None
    ):
        """
        Initialize content extraction error.

        Args:
            message: Error message
            filepath: Path to the file
            content_type: Type of content that failed to extract (e.g., 'speaker', 'body_text')
        """
        super().__init__(message, filepath, "content_extraction")
        if content_type:
            self.details["content_type"] = content_type
        self.content_type: Optional[str] = content_type


class MetadataExtractionError(FileProcessingError):
    """Raised when metadata extraction from filenames fails."""

    def __init__(self, message: str, filepath: Optional[str] = None, pattern: Optional[str] = None):
        """
        Initialize metadata extraction error.

        Args:
            message: Error message
            filepath: Path to the file
            pattern: The regex pattern that failed to match
        """
        super().__init__(message, filepath, "metadata_extraction")
        if pattern:
            self.details["pattern"] = pattern
        self.pattern: Optional[str] = pattern


class APIError(ClassifierError):
    """Raised when API operations fail."""

    def __init__(
        self,
        message: str,
        api_provider: Optional[str] = None,
        status_code: Optional[int] = None,
        response_text: Optional[str] = None,
    ):
        """
        Initialize API error.

        Args:
            message: Error message
            api_provider: The API provider (e.g., 'OpenAI')
            status_code: HTTP status code if applicable
            response_text: Raw response text from the API
        """
        details: Dict[str, Any] = {}
        if api_provider:
            details["api_provider"] = api_provider
        if status_code:
            details["status_code"] = status_code
        if response_text:
            details["response_text"] = (
                response_text[:200] + "..." if len(response_text) > 200 else response_text
            )

        super().__init__(message, details)
        self.api_provider: Optional[str] = api_provider
        self.status_code: Optional[int] = status_code
        self.response_text: Optional[str] = response_text


class ClassificationError(APIError):
    """Raised when LLM classification fails."""

    def __init__(
        self, message: str, model: Optional[str] = None, prompt_length: Optional[int] = None
    ):
        """
        Initialize classification error.

        Args:
            message: Error message
            model: The model used for classification
            prompt_length: Length of the prompt that failed
        """
        super().__init__(message, api_provider="OpenAI")
        if model:
            self.details["model"] = model
        if prompt_length:
            self.details["prompt_length"] = prompt_length
        self.model: Optional[str] = model
        self.prompt_length: Optional[int] = prompt_length


class ValidationError(ClassifierError):
    """Raised when data validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        expected_type: Optional[str] = None,
    ):
        """
        Initialize validation error.

        Args:
            message: Error message
            field: The field that failed validation
            value: The invalid value
            expected_type: The expected type or format
        """
        details: Dict[str, Any] = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)
        if expected_type:
            details["expected_type"] = expected_type

        super().__init__(message, details)
        self.field: Optional[str] = field
        self.value: Optional[Any] = value
        self.expected_type: Optional[str] = expected_type


class CSVError(ClassifierError):
    """Raised when CSV operations fail."""

    def __init__(
        self,
        message: str,
        filepath: Optional[str] = None,
        operation: Optional[str] = None,
        row_number: Optional[int] = None,
    ):
        """
        Initialize CSV error.

        Args:
            message: Error message
            filepath: Path to the CSV file
            operation: The CSV operation that failed (e.g., 'read', 'write', 'parse')
            row_number: Row number where the error occurred
        """
        details: Dict[str, Any] = {}
        if filepath:
            details["filepath"] = filepath
        if operation:
            details["operation"] = operation
        if row_number:
            details["row_number"] = row_number

        super().__init__(message, details)
        self.filepath: Optional[str] = filepath
        self.operation: Optional[str] = operation
        self.row_number: Optional[int] = row_number


class TemplateError(ClassifierError):
    """Raised when template operations fail."""

    def __init__(
        self, message: str, template_name: Optional[str] = None, template_path: Optional[str] = None
    ):
        """
        Initialize template error.

        Args:
            message: Error message
            template_name: Name of the template that failed
            template_path: Path to the template file
        """
        details: Dict[str, Any] = {}
        if template_name:
            details["template_name"] = template_name
        if template_path:
            details["template_path"] = template_path

        super().__init__(message, details)
        self.template_name: Optional[str] = template_name
        self.template_path: Optional[str] = template_path


class CacheError(ClassifierError):
    """Raised when cache operations fail."""

    def __init__(
        self, message: str, cache_key: Optional[str] = None, operation: Optional[str] = None
    ):
        """
        Initialize cache error.

        Args:
            message: Error message
            cache_key: The cache key involved in the error
            operation: The cache operation that failed (e.g., 'get', 'set', 'clear')
        """
        details: Dict[str, Any] = {}
        if cache_key:
            details["cache_key"] = cache_key
        if operation:
            details["operation"] = operation

        super().__init__(message, details)
        self.cache_key: Optional[str] = cache_key
        self.operation: Optional[str] = operation


# Convenience functions for common error scenarios


def raise_config_error(
    message: str, config_key: Optional[str] = None, config_value: Optional[Any] = None
) -> None:
    """Raise a configuration error with standard formatting."""
    raise ConfigurationError(message, config_key, config_value)


def raise_file_error(
    message: str, filepath: Optional[str] = None, operation: Optional[str] = None
) -> None:
    """Raise a file processing error with standard formatting."""
    raise FileProcessingError(message, filepath, operation)


def raise_api_error(
    message: str, api_provider: str = "OpenAI", status_code: Optional[int] = None
) -> None:
    """Raise an API error with standard formatting."""
    raise APIError(message, api_provider, status_code)


def raise_validation_error(
    message: str, field: Optional[str] = None, value: Optional[Any] = None
) -> None:
    """Raise a validation error with standard formatting."""
    raise ValidationError(message, field, value)
