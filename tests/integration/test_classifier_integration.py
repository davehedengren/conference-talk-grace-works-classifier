"""
Integration tests for the refactored classifier.

These tests verify the complete workflow from file processing to CSV output.
"""

import csv
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest

# Import the functions we want to test
from classifier_refactored import (
    create_classifier_config,
    determine_files_to_process,
    main,
    parse_arguments,
    process_single_talk,
    process_talks_with_incremental_write,
    setup_openai_and_template,
)
from models import Classification, ClassifierConfig


@pytest.fixture
def integration_config(tmp_path: Path) -> ClassifierConfig:
    """Create a complete test configuration for integration tests."""
    talks_dir = tmp_path / "conference_talks"
    output_dir = tmp_path / "output"
    templates_dir = tmp_path / "templates"

    # Create directories
    talks_dir.mkdir()
    output_dir.mkdir()
    templates_dir.mkdir()

    # Create a template file
    template_file = templates_dir / "classify_prompt.jinja"
    template_file.write_text(
        """
Title: {{ title }}
Speaker: {{ speaker }}
Conference: {{ conference }}
Date: {{ date }}

Content:
{{ content }}

Please classify this talk on a scale from -3 to +3 based on its emphasis on grace vs works.
Return a JSON object with "score", "explanation", and "key_phrases".
"""
    )

    # Create some sample talk files
    sample_talks = [
        (
            "2024-04-salvation-grace_john-smith.html",
            """
        <!DOCTYPE html>
        <html>
        <body>
            <p class="author-name">By Elder John Smith</p>
            <div class="body-content">
                <p>We are saved by grace through faith, not by works.</p>
                <p>The grace of Jesus Christ is sufficient for all.</p>
            </div>
        </body>
        </html>
        """,
        ),
        (
            "2024-10-commandments-obedience_jane-doe.html",
            """
        <!DOCTYPE html>
        <html>
        <body>
            <p class="author-name">By Sister Jane Doe</p>
            <div class="body-content">
                <p>Keep the commandments and follow the prophet.</p>
                <p>Obedience is the first law of heaven.</p>
            </div>
        </body>
        </html>
        """,
        ),
        (
            "2023-04-faith-works_mary-johnson.html",
            """
        <!DOCTYPE html>
        <html>
        <body>
            <p class="author-name">By President Mary Johnson</p>
            <div class="body-content">
                <p>Faith without works is dead.</p>
                <p>We must have both faith and good works.</p>
            </div>
        </body>
        </html>
        """,
        ),
    ]

    for filename, content in sample_talks:
        talk_file = talks_dir / filename
        talk_file.write_text(content)

    return ClassifierConfig(
        talks_dir=talks_dir,
        output_dir=output_dir,
        templates_dir=templates_dir,
        openai_api_key="test-key",
        openai_model="test-model",
        batch_size=2,
    )


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client that returns predictable responses."""
    mock_client = Mock()

    def mock_completion_response(messages, **kwargs):
        # Create different responses based on content
        content = messages[1]["content"] if len(messages) > 1 else ""

        if "grace" in content.lower():
            response_text = '{"score": -2, "explanation": "Heavy emphasis on grace", "key_phrases": ["grace", "faith"]}'
        elif "commandments" in content.lower() or "obedience" in content.lower():
            response_text = '{"score": 2, "explanation": "Heavy emphasis on works", "key_phrases": ["commandments", "obedience"]}'
        else:
            response_text = '{"score": 0, "explanation": "Balanced approach", "key_phrases": ["faith", "works"]}'

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = response_text
        return mock_response

    mock_client.chat.completions.create.side_effect = mock_completion_response
    return mock_client


def test_create_classifier_config_success(tmp_path: Path):
    """Test successful configuration creation."""
    # Create required directories
    talks_dir = tmp_path / "conference_talks"
    output_dir = tmp_path / "output"
    templates_dir = tmp_path / "templates"

    talks_dir.mkdir()
    output_dir.mkdir()
    templates_dir.mkdir()

    with patch.dict(
        os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "o4-mini-2025-04-16"}
    ):
        with patch("classifier_refactored.Path") as mock_path:
            # Mock Path calls to return our test directories
            def path_side_effect(path_str):
                if path_str == "conference_talks":
                    return talks_dir
                elif path_str == "output":
                    return output_dir
                elif path_str == "templates":
                    return templates_dir
                return Path(path_str)

            mock_path.side_effect = path_side_effect

            config = create_classifier_config()
            assert config.openai_api_key == "test-key"
            assert config.openai_model == "o4-mini-2025-04-16"


def test_create_classifier_config_missing_api_key(tmp_path: Path):
    """Test configuration creation with missing API key."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("classifier_refactored.Path") as mock_path:
            mock_path.side_effect = lambda x: tmp_path / x

            with pytest.raises(ValueError, match="Configuration errors"):
                create_classifier_config()


def test_determine_files_to_process_single_file(integration_config: ClassifierConfig):
    """Test file determination for single file processing."""
    # Mock args with single file
    args = Mock()
    args.file = str(integration_config.talks_dir / "2024-04-salvation-grace_john-smith.html")
    args.num_talks = None

    processed_filenames = set()

    files = determine_files_to_process(integration_config, args, processed_filenames)

    assert len(files) == 1
    assert files[0].name == "2024-04-salvation-grace_john-smith.html"


def test_determine_files_to_process_resume_filtering(integration_config: ClassifierConfig):
    """Test file determination with resume filtering."""
    args = Mock()
    args.file = None
    args.num_talks = None

    # Simulate one file already processed
    processed_filenames = {"2024-04-salvation-grace_john-smith.html"}

    files = determine_files_to_process(integration_config, args, processed_filenames)

    assert len(files) == 2  # Should exclude the processed file
    filenames = [f.name for f in files]
    assert "2024-04-salvation-grace_john-smith.html" not in filenames
    assert "2024-10-commandments-obedience_jane-doe.html" in filenames
    assert "2023-04-faith-works_mary-johnson.html" in filenames


def test_determine_files_to_process_num_talks_limit(integration_config: ClassifierConfig):
    """Test file determination with number limit."""
    args = Mock()
    args.file = None
    args.num_talks = 2

    processed_filenames = set()

    files = determine_files_to_process(integration_config, args, processed_filenames)

    assert len(files) == 2


@patch("classifier_refactored.Environment")
def test_setup_openai_and_template(mock_env, integration_config: ClassifierConfig):
    """Test OpenAI client and template setup."""
    # Mock the template loading
    mock_template = Mock()
    mock_jinja_env = Mock()
    mock_jinja_env.get_template.return_value = mock_template
    mock_env.return_value = mock_jinja_env

    with patch("classifier_refactored.OpenAI") as mock_openai:
        mock_client = Mock()
        mock_openai.return_value = mock_client

        client, template = setup_openai_and_template(integration_config)

        assert client == mock_client
        assert template == mock_template
        mock_openai.assert_called_once_with(api_key="test-key")


def test_process_single_talk_success(integration_config: ClassifierConfig, mock_openai_client):
    """Test successful processing of a single talk."""
    from jinja2 import Template

    template = Template("{{ content }}")
    filepath = integration_config.talks_dir / "2024-04-salvation-grace_john-smith.html"

    result = process_single_talk(
        filepath, integration_config, template, mock_openai_client, "test-model"
    )

    assert result is not None
    assert result["filename"] == "2024-04-salvation-grace_john-smith.html"
    assert result["year"] == "2024"
    assert result["month"] == "04"
    assert result["speaker_name"] == "John Smith"
    assert result["score"] == -2  # Based on mock response for grace content
    assert "grace" in result["explanation"].lower()
    assert result["model_used"] == "test-model"


def test_process_single_talk_file_error(integration_config: ClassifierConfig, mock_openai_client):
    """Test processing of a talk with file read error."""
    from jinja2 import Template

    template = Template("{{ content }}")
    # Non-existent file
    filepath = integration_config.talks_dir / "nonexistent.html"

    result = process_single_talk(
        filepath, integration_config, template, mock_openai_client, "test-model"
    )

    assert result is None


def test_process_talks_with_incremental_write(
    integration_config: ClassifierConfig, mock_openai_client
):
    """Test processing multiple talks with incremental CSV writing."""
    from jinja2 import Template

    template = Template("{{ content }}")
    files_to_process = [
        integration_config.talks_dir / "2024-04-salvation-grace_john-smith.html",
        integration_config.talks_dir / "2024-10-commandments-obedience_jane-doe.html",
    ]

    output_csv_path = integration_config.output_dir / "test_output.csv"

    process_talks_with_incremental_write(
        files_to_process,
        integration_config,
        template,
        mock_openai_client,
        "test-model",
        output_csv_path,
        False,  # No resumed data
    )

    # Verify CSV was created and contains data
    assert output_csv_path.exists()

    with open(output_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2

    # Check first row (grace talk)
    grace_row = next((row for row in rows if "john-smith" in row["filename"]), None)
    assert grace_row is not None
    assert grace_row["score"] == "-2"
    assert grace_row["speaker_name"] == "John Smith"

    # Check second row (works talk)
    works_row = next((row for row in rows if "jane-doe" in row["filename"]), None)
    assert works_row is not None
    assert works_row["score"] == "2"
    assert works_row["speaker_name"] == "Jane Doe"


def test_main_integration_with_mocks(integration_config: ClassifierConfig):
    """Test the main function with complete workflow mocking."""
    test_args = ["classifier_refactored.py", "--num-talks", "2"]

    with patch("sys.argv", test_args):
        with patch("classifier_refactored.create_classifier_config") as mock_config:
            with patch("classifier_refactored.setup_openai_and_template") as mock_setup:
                with patch(
                    "classifier_refactored.process_talks_with_incremental_write"
                ) as mock_process:
                    with patch("classifier_refactored.analyze_grace_works_balance") as mock_analyze:
                        # Setup mocks
                        mock_config.return_value = integration_config

                        mock_client = Mock()
                        mock_template = Mock()
                        mock_setup.return_value = (mock_client, mock_template)

                        # Run main
                        main()

                        # Verify calls
                        mock_config.assert_called_once()
                        mock_setup.assert_called_once()
                        mock_process.assert_called_once()


def test_resume_functionality_integration(integration_config: ClassifierConfig):
    """Test the resume functionality with a pre-existing CSV."""
    # Create a pre-existing CSV with one processed talk
    existing_csv = integration_config.output_dir / "existing.csv"
    existing_data = [
        {
            "filename": "2024-04-salvation-grace_john-smith.html",
            "year": "2024",
            "month": "04",
            "conference_session_id": "2024-04",
            "talk_identifier": "salvation-grace",
            "speaker_name": "John Smith",
            "text_preview": "Preview text...",
            "score": -1,
            "explanation": "Previous explanation",
            "key_phrases": "grace, faith",
            "model_used": "previous-model",
        }
    ]

    fieldnames = [
        "filename",
        "year",
        "month",
        "conference_session_id",
        "talk_identifier",
        "speaker_name",
        "text_preview",
        "score",
        "explanation",
        "key_phrases",
        "model_used",
    ]

    with open(existing_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_data)

    test_args = ["classifier_refactored.py", "--resume-from-csv", str(existing_csv)]

    with patch("sys.argv", test_args):
        with patch("classifier_refactored.create_classifier_config") as mock_config:
            with patch("classifier_refactored.setup_openai_and_template") as mock_setup:
                with patch("classifier_refactored.determine_files_to_process") as mock_determine:
                    with patch(
                        "classifier_refactored.process_talks_with_incremental_write"
                    ) as mock_process:
                        # Setup mocks
                        mock_config.return_value = integration_config
                        mock_client = Mock()
                        mock_template = Mock()
                        mock_setup.return_value = (mock_client, mock_template)

                        # Should only return files not in the resume CSV
                        remaining_files = [
                            integration_config.talks_dir
                            / "2024-10-commandments-obedience_jane-doe.html",
                            integration_config.talks_dir / "2023-04-faith-works_mary-johnson.html",
                        ]
                        mock_determine.return_value = remaining_files

                        # Run main
                        main()

                        # Verify that determine_files_to_process was called with the processed filename
                        args, kwargs = mock_determine.call_args
                        processed_filenames = args[2]  # Third argument is processed_filenames
                        assert "2024-04-salvation-grace_john-smith.html" in processed_filenames


@patch("classifier_refactored.create_classifier_config")
def test_configuration_error_handling(mock_config):
    """Test that configuration errors are properly handled."""
    mock_config.side_effect = ValueError("Test configuration error")

    # Should not raise an exception, should print error and return
    main()  # Should complete without crashing


if __name__ == "__main__":
    pytest.main([__file__])
