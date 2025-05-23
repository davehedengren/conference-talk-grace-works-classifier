"""
File processing functions for the Conference Talk Grace-Works Classifier.

This module contains type-hinted versions of the file processing functions.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bs4 import BeautifulSoup, Tag

from models import ProcessingResult, TalkContent, TalkMetadata


def get_talk_files(directory: Path) -> List[Path]:
    """
    Gets a list of .html files from the specified directory.

    Args:
        directory: Path to the directory containing talk files

    Returns:
        List of Path objects for HTML files found
    """
    files: List[Path] = []
    if not directory.exists():
        print(f"Error: Directory '{directory}' not found.")
        return files

    for filepath in directory.iterdir():
        if filepath.suffix == ".html" and not filepath.name.startswith("."):
            files.append(filepath)
    return files


def extract_metadata_from_filename(filename: str, pattern: str) -> Optional[TalkMetadata]:
    """
    Extracts metadata from a talk filename using regex pattern.

    Args:
        filename: The filename to parse
        pattern: Regex pattern for parsing

    Returns:
        TalkMetadata object if parsing succeeds, None otherwise
    """
    filename_pattern = re.compile(pattern)
    match = filename_pattern.match(os.path.basename(filename))

    if match:
        year, month, talk_identifier, speaker_from_filename = match.groups()
        conference_session_id = f"{year}-{month}"

        return TalkMetadata(
            year=year,
            month=month,
            conference_session_id=conference_session_id,
            talk_identifier=talk_identifier,
            speaker_name_from_filename=speaker_from_filename,
            filename=os.path.basename(filename),
        )

    print(f"Warning: Could not extract metadata from filename: {filename}")
    return None


def extract_body_text_and_speaker(filepath: Path) -> ProcessingResult[Dict[str, Any]]:
    """
    Extracts body text and speaker name from HTML file using BeautifulSoup.

    Args:
        filepath: Path to the HTML file

    Returns:
        ProcessingResult containing TalkContent if successful
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

            # Extract speaker name
            speaker_name_from_html = _extract_speaker_name(soup)

            # Extract body text
            text_content = _extract_body_text(soup)

            talk_content = TalkContent(
                text_content=text_content, speaker_name_from_html=speaker_name_from_html
            )

            return ProcessingResult(success=True, data={"content": talk_content})

    except Exception as e:
        error_msg = f"Error reading or parsing file {filepath}: {e}"
        print(error_msg)
        return ProcessingResult(success=False, error_message=error_msg)


def _extract_speaker_name(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract and clean speaker name from HTML.

    Args:
        soup: BeautifulSoup object of the HTML

    Returns:
        Cleaned speaker name or None if not found
    """
    speaker_tag: Optional[Tag] = soup.find("p", class_="author-name")
    if not speaker_tag:
        return None

    raw_speaker_text: str = speaker_tag.get_text(strip=False)

    # Clean the speaker name
    cleaned_name = raw_speaker_text
    cleaned_name = cleaned_name.replace("Â\\xa0", " ")  # Replace Â and non-breaking space
    cleaned_name = cleaned_name.replace("Â", "")  # Replace just Â if it exists

    # Remove prefixes - order matters here, longer ones first
    prefixes_to_remove = ["By Elder ", "By Sister ", "By President ", "By "]

    for prefix in prefixes_to_remove:
        if cleaned_name.startswith(prefix):
            cleaned_name = cleaned_name[len(prefix) :]
            break  # Remove only the first matching prefix

    return cleaned_name.strip()


def _extract_body_text(soup: BeautifulSoup) -> str:
    """
    Extract clean body text from HTML.

    Args:
        soup: BeautifulSoup object of the HTML

    Returns:
        Cleaned text content
    """
    # Remove script and style elements for body text extraction
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()

    # Get text and clean it up
    text_content: str = soup.get_text()
    lines = (line.strip() for line in text_content.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text_content = "\\n".join(chunk for chunk in chunks if chunk)

    return text_content
