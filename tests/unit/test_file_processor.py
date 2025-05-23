"""
Unit tests for the file processor module.
"""

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from models import TalkContent, TalkMetadata
from processors.file_processor import (
    _extract_body_text,
    _extract_speaker_name,
    extract_body_text_and_speaker,
    extract_metadata_from_filename,
    get_talk_files,
)


def test_get_talk_files(tmp_path: Path) -> None:
    """Test getting HTML files from a directory."""
    # Create test files
    (tmp_path / "test1.html").write_text("<html></html>")
    (tmp_path / "test2.html").write_text("<html></html>")
    (tmp_path / "test.txt").write_text("not html")
    (tmp_path / ".hidden.html").write_text("<html></html>")

    files = get_talk_files(tmp_path)

    assert len(files) == 2
    filenames = [f.name for f in files]
    assert "test1.html" in filenames
    assert "test2.html" in filenames
    assert "test.txt" not in filenames
    assert ".hidden.html" not in filenames


def test_get_talk_files_nonexistent_directory(tmp_path: Path) -> None:
    """Test handling of nonexistent directory."""
    nonexistent = tmp_path / "nonexistent"
    files = get_talk_files(nonexistent)
    assert files == []


def test_extract_metadata_from_filename_success() -> None:
    """Test successful metadata extraction from filename."""
    filename = "2024-04-salvation-grace_john-smith.html"
    pattern = r"(\d{4})-(\d{2})-([^._]+)(?:_([a-zA-Z0-9\-]+))?\.html"

    metadata = extract_metadata_from_filename(filename, pattern)

    assert metadata is not None
    assert metadata.year == "2024"
    assert metadata.month == "04"
    assert metadata.conference_session_id == "2024-04"
    assert metadata.talk_identifier == "salvation-grace"
    assert metadata.speaker_name_from_filename == "john-smith"
    assert metadata.filename == filename


def test_extract_metadata_from_filename_without_speaker() -> None:
    """Test metadata extraction from filename without speaker."""
    filename = "2024-10-faith-works.html"
    pattern = r"(\d{4})-(\d{2})-([^._]+)(?:_([a-zA-Z0-9\-]+))?\.html"

    metadata = extract_metadata_from_filename(filename, pattern)

    assert metadata is not None
    assert metadata.year == "2024"
    assert metadata.month == "10"
    assert metadata.conference_session_id == "2024-10"
    assert metadata.talk_identifier == "faith-works"
    assert metadata.speaker_name_from_filename is None
    assert metadata.filename == filename


def test_extract_metadata_from_filename_failure() -> None:
    """Test handling of invalid filename format."""
    filename = "invalid-filename.html"
    pattern = r"(\d{4})-(\d{2})-([^._]+)(?:_([a-zA-Z0-9\-]+))?\.html"

    metadata = extract_metadata_from_filename(filename, pattern)

    assert metadata is None


def test_extract_speaker_name() -> None:
    """Test speaker name extraction and cleaning."""
    html = """
    <html>
    <body>
        <p class="author-name">By Elder John Test Speaker</p>
    </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")

    speaker_name = _extract_speaker_name(soup)

    assert speaker_name == "John Test Speaker"


def test_extract_speaker_name_with_cleaning() -> None:
    """Test speaker name extraction with character cleaning."""
    html = """
    <html>
    <body>
        <p class="author-name">By Sister Â Jane Doe</p>
    </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")

    speaker_name = _extract_speaker_name(soup)

    assert speaker_name == "Jane Doe"


def test_extract_speaker_name_no_tag() -> None:
    """Test handling when no speaker tag is found."""
    html = "<html><body><p>No speaker tag</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")

    speaker_name = _extract_speaker_name(soup)

    assert speaker_name is None


def test_extract_body_text() -> None:
    """Test body text extraction and cleaning."""
    html = """
    <html>
    <body>
        <script>alert('test');</script>
        <style>body { color: red; }</style>
        <p>This is the main content.</p>
        <p>This is another paragraph.</p>
    </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")

    text = _extract_body_text(soup)

    assert "This is the main content." in text
    assert "This is another paragraph." in text
    assert "alert('test');" not in text
    assert "color: red;" not in text


def test_extract_body_text_and_speaker_success(temp_talk_file: Path) -> None:
    """Test successful extraction of body text and speaker."""
    result = extract_body_text_and_speaker(temp_talk_file)

    assert result.success is True
    assert result.data is not None

    content = result.data["content"]
    assert isinstance(content, TalkContent)
    assert "grace and works" in content.text_content
    assert content.speaker_name_from_html == "John Test Speaker"


def test_extract_body_text_and_speaker_file_not_found(tmp_path: Path) -> None:
    """Test handling of nonexistent file."""
    nonexistent_file = tmp_path / "nonexistent.html"

    result = extract_body_text_and_speaker(nonexistent_file)

    assert result.success is False
    assert result.error_message is not None
    assert "Error reading or parsing file" in result.error_message
