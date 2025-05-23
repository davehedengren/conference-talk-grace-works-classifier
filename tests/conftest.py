"""
Pytest configuration and fixtures for the Conference Talk Grace-Works Classifier tests.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

from models import Classification, ClassifierConfig, TalkContent, TalkMetadata


@pytest.fixture
def sample_talk_html() -> str:
    """Sample HTML content for testing talk processing."""
    return """
    <!DOCTYPE html>
    <html>
    <body>
        <p class="author-name">By Elder John Test Speaker</p>
        <div class="body-content">
            <p>This is a sample talk about grace and works. We learn that through 
            the grace of Jesus Christ, we are saved after all we can do. However, 
            we must also remember that faith without works is dead.</p>
            <p>The commandments are given to help us become like our Heavenly Father. 
            By following them, we demonstrate our love for God and our commitment 
            to His plan.</p>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def temp_talk_file(tmp_path: Path, sample_talk_html: str) -> Path:
    """Create a temporary talk file for testing."""
    file_path = tmp_path / "2024-04-test-talk_john-smith.html"
    file_path.write_text(sample_talk_html)
    return file_path


@pytest.fixture
def sample_classification() -> Classification:
    """Sample classification result for testing."""
    return Classification(
        score=1,
        explanation="This talk balances grace and works, with a slight emphasis on works through following commandments.",
        key_phrases=["grace", "works", "commandments", "faith"],
        model_used="test-model",
    )


@pytest.fixture
def sample_talk_metadata() -> TalkMetadata:
    """Sample talk metadata for testing."""
    return TalkMetadata(
        year="2024",
        month="04",
        conference_session_id="2024-04",
        talk_identifier="test-talk",
        speaker_name_from_filename="john-smith",
        filename="2024-04-test-talk_john-smith.html",
    )


@pytest.fixture
def sample_talk_content() -> TalkContent:
    """Sample talk content for testing."""
    return TalkContent(
        text_content="This is a sample talk about grace and works...",
        speaker_name_from_html="John Test Speaker",
    )


@pytest.fixture
def test_config(tmp_path: Path) -> ClassifierConfig:
    """Test configuration with temporary directories."""
    talks_dir = tmp_path / "conference_talks"
    output_dir = tmp_path / "output"
    templates_dir = tmp_path / "templates"

    # Create directories
    talks_dir.mkdir()
    output_dir.mkdir()
    templates_dir.mkdir()

    # Create a simple template file
    template_file = templates_dir / "classify_prompt.jinja"
    template_file.write_text(
        """
Title: {{ title }}
Speaker: {{ speaker }}
Conference: {{ conference }}
Date: {{ date }}

Content:
{{ content }}

Please classify this talk on a scale from -3 to +3...
"""
    )

    return ClassifierConfig(
        talks_dir=talks_dir,
        output_dir=output_dir,
        templates_dir=templates_dir,
        openai_api_key="test-key",
        openai_model="test-model",
    )


@pytest.fixture
def mock_openai_response() -> Dict[str, Any]:
    """Mock OpenAI API response for testing."""
    return {
        "choices": [
            {
                "message": {
                    "content": '{"score": 1, "explanation": "Test explanation", "key_phrases": ["grace", "works"]}'
                }
            }
        ]
    }
