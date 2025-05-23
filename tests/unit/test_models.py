"""
Unit tests for the domain models.
"""

from pathlib import Path

import pytest

from models import (
    Classification,
    ClassifierConfig,
    ProcessingResult,
    TalkContent,
    TalkData,
    TalkMetadata,
)


def test_talk_metadata_creation() -> None:
    """Test TalkMetadata creation and fields."""
    metadata = TalkMetadata(
        year="2024",
        month="04",
        conference_session_id="2024-04",
        talk_identifier="test-talk",
        speaker_name_from_filename="john-smith",
        filename="2024-04-test-talk_john-smith.html",
    )

    assert metadata.year == "2024"
    assert metadata.month == "04"
    assert metadata.conference_session_id == "2024-04"
    assert metadata.talk_identifier == "test-talk"
    assert metadata.speaker_name_from_filename == "john-smith"
    assert metadata.filename == "2024-04-test-talk_john-smith.html"


def test_classification_creation() -> None:
    """Test Classification creation and fields."""
    classification = Classification(
        score=2,
        explanation="This talk emphasizes works and commandments.",
        key_phrases=["commandments", "obedience", "works"],
        model_used="gpt-4",
    )

    assert classification.score == 2
    assert classification.explanation == "This talk emphasizes works and commandments."
    assert classification.key_phrases == ["commandments", "obedience", "works"]
    assert classification.model_used == "gpt-4"


def test_processing_result_success() -> None:
    """Test ProcessingResult for successful operation."""
    result = ProcessingResult(success=True, data={"key": "value"}, error_message=None)

    assert result.success is True
    assert result.data == {"key": "value"}
    assert result.error_message is None


def test_processing_result_failure() -> None:
    """Test ProcessingResult for failed operation."""
    result = ProcessingResult(success=False, data=None, error_message="Something went wrong")

    assert result.success is False
    assert result.data is None
    assert result.error_message == "Something went wrong"


def test_talk_content_creation() -> None:
    """Test TalkContent creation and fields."""
    content = TalkContent(
        text_content="This is the talk content about grace and works.",
        speaker_name_from_html="Elder John Smith",
    )

    assert content.text_content == "This is the talk content about grace and works."
    assert content.speaker_name_from_html == "Elder John Smith"


def test_talk_data_creation() -> None:
    """Test TalkData creation and fields."""
    talk_data = TalkData(
        filename="2024-04-test.html",
        year="2024",
        month="04",
        conference_session_id="2024-04",
        talk_identifier="test",
        speaker_name="John Smith",
        text_preview="This is a preview...",
        score=1,
        explanation="Balanced talk",
        key_phrases="grace, works, faith",
        model_used="gpt-4",
    )

    assert talk_data.filename == "2024-04-test.html"
    assert talk_data.year == "2024"
    assert talk_data.score == 1
    assert talk_data.key_phrases == "grace, works, faith"


def test_classifier_config_creation(tmp_path: Path) -> None:
    """Test ClassifierConfig creation and fields."""
    talks_dir = tmp_path / "talks"
    output_dir = tmp_path / "output"
    templates_dir = tmp_path / "templates"

    # Create directories
    talks_dir.mkdir()
    output_dir.mkdir()
    templates_dir.mkdir()

    config = ClassifierConfig(
        talks_dir=talks_dir,
        output_dir=output_dir,
        templates_dir=templates_dir,
        openai_api_key="test-key",
        openai_model="gpt-4",
    )

    assert config.talks_dir == talks_dir
    assert config.output_dir == output_dir
    assert config.templates_dir == templates_dir
    assert config.openai_api_key == "test-key"
    assert config.openai_model == "gpt-4"
    assert config.batch_size == 10  # default value


def test_classifier_config_validate_success(tmp_path: Path) -> None:
    """Test ClassifierConfig validation when all is correct."""
    talks_dir = tmp_path / "talks"
    output_dir = tmp_path / "output"
    templates_dir = tmp_path / "templates"

    # Create directories
    talks_dir.mkdir()
    output_dir.mkdir()
    templates_dir.mkdir()

    config = ClassifierConfig(
        talks_dir=talks_dir,
        output_dir=output_dir,
        templates_dir=templates_dir,
        openai_api_key="test-key",
    )

    errors = config.validate()
    assert errors == []


def test_classifier_config_validate_missing_api_key(tmp_path: Path) -> None:
    """Test ClassifierConfig validation with missing API key."""
    talks_dir = tmp_path / "talks"
    output_dir = tmp_path / "output"
    templates_dir = tmp_path / "templates"

    # Create directories
    talks_dir.mkdir()
    output_dir.mkdir()
    templates_dir.mkdir()

    config = ClassifierConfig(
        talks_dir=talks_dir, output_dir=output_dir, templates_dir=templates_dir, openai_api_key=None
    )

    errors = config.validate()
    assert "OPENAI_API_KEY is required" in errors


def test_classifier_config_validate_missing_directories(tmp_path: Path) -> None:
    """Test ClassifierConfig validation with missing directories."""
    talks_dir = tmp_path / "nonexistent_talks"
    output_dir = tmp_path / "output"
    templates_dir = tmp_path / "nonexistent_templates"

    # Create only output directory
    output_dir.mkdir()

    config = ClassifierConfig(
        talks_dir=talks_dir,
        output_dir=output_dir,
        templates_dir=templates_dir,
        openai_api_key="test-key",
    )

    errors = config.validate()
    assert len(errors) == 2
    assert any("Talks directory does not exist" in error for error in errors)
    assert any("Templates directory does not exist" in error for error in errors)
