"""
Domain models for the Conference Talk Grace-Works Classifier.

This module defines the core data structures used throughout the application.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

T = TypeVar("T")


@dataclass
class TalkMetadata:
    """Metadata extracted from a conference talk file."""

    year: Optional[str]
    month: Optional[str]
    conference_session_id: Optional[str]
    talk_identifier: Optional[str]
    speaker_name_from_filename: Optional[str]
    filename: str


@dataclass
class Classification:
    """Result of LLM classification of a talk."""

    score: int
    explanation: str
    key_phrases: List[str]
    model_used: str


@dataclass
class ProcessingResult(Generic[T]):
    """Result of processing a single operation with error handling."""

    success: bool
    data: Optional[T] = None
    error_message: Optional[str] = None


@dataclass
class TalkContent:
    """Extracted content from a talk file."""

    text_content: str
    speaker_name_from_html: Optional[str]


@dataclass
class TalkData:
    """Complete data for a processed talk."""

    filename: str
    year: Optional[str]
    month: Optional[str]
    conference_session_id: Optional[str]
    talk_identifier: Optional[str]
    speaker_name: Optional[str]
    text_preview: str
    score: int
    explanation: str
    key_phrases: str  # Comma-separated string for CSV compatibility
    model_used: str


@dataclass
class ClassifierConfig:
    """Configuration settings for the classifier."""

    # File paths
    talks_dir: Path
    output_dir: Path
    templates_dir: Path

    # Processing settings
    batch_size: int = 10
    text_preview_length: int = 100

    # API settings
    openai_api_key: Optional[str] = None
    openai_model: str = "o4-mini-2025-04-16"

    # Regex pattern for filename parsing (includes dashes in speaker names)
    filename_pattern: str = r"(\d{4})-(\d{2})-([^._]+)(?:_([a-zA-Z0-9\-]+))?\.html"

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required")
        if not self.talks_dir.exists():
            errors.append(f"Talks directory does not exist: {self.talks_dir}")
        if not self.templates_dir.exists():
            errors.append(f"Templates directory does not exist: {self.templates_dir}")
        return errors
