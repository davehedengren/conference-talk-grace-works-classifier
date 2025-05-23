"""
Unit tests for the CSV manager module.
"""

import csv
from pathlib import Path
from typing import Any, Dict, List

import pytest

from processors.csv_manager import (
    analyze_grace_works_balance,
    load_processed_talks_from_csv,
    write_to_csv,
)


def test_write_to_csv_with_header(tmp_path: Path) -> None:
    """Test writing CSV with header."""
    csv_file = tmp_path / "test.csv"
    test_data = [
        {
            "filename": "test1.html",
            "year": "2024",
            "month": "04",
            "conference_session_id": "2024-04",
            "talk_identifier": "test",
            "speaker_name": "Test Speaker",
            "text_preview": "Preview text",
            "score": 1,
            "explanation": "Test explanation",
            "key_phrases": "grace, works",
            "model_used": "test-model",
        }
    ]

    write_to_csv(test_data, csv_file, write_header=True)

    assert csv_file.exists()

    # Verify the content
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["filename"] == "test1.html"
    assert rows[0]["score"] == "1"


def test_write_to_csv_append(tmp_path: Path) -> None:
    """Test appending to existing CSV."""
    csv_file = tmp_path / "test.csv"

    # Write initial data with header
    initial_data = [{"filename": "test1.html", "score": "1"}]
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "score"])
        writer.writeheader()
        writer.writerows(initial_data)

    # Append new data
    new_data = [
        {
            "filename": "test2.html",
            "year": "2024",
            "month": "04",
            "conference_session_id": "2024-04",
            "talk_identifier": "test2",
            "speaker_name": "Test Speaker 2",
            "text_preview": "Preview text 2",
            "score": 2,
            "explanation": "Test explanation 2",
            "key_phrases": "commandments",
            "model_used": "test-model",
        }
    ]

    write_to_csv(new_data, csv_file, write_header=False)

    # Verify the content
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 2
    assert rows[1]["filename"] == "test2.html"


def test_write_to_csv_empty_data(tmp_path: Path) -> None:
    """Test writing empty data does nothing."""
    csv_file = tmp_path / "test.csv"

    write_to_csv([], csv_file, write_header=True)

    assert not csv_file.exists()


def test_load_processed_talks_from_csv_success(tmp_path: Path) -> None:
    """Test loading processed talks from CSV."""
    csv_file = tmp_path / "test.csv"

    # Create test CSV
    test_data = [
        ["filename", "explanation"],
        ["test1.html", "Good explanation"],
        ["test2.html", "Error parsing LLM response"],  # Should be skipped
        ["test3.html", "Another good explanation"],
    ]

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(test_data)

    processed_files, successful_rows = load_processed_talks_from_csv(csv_file)

    assert len(processed_files) == 2
    assert "test1.html" in processed_files
    assert "test3.html" in processed_files
    assert "test2.html" not in processed_files

    assert len(successful_rows) == 2


def test_load_processed_talks_from_csv_file_not_found(tmp_path: Path) -> None:
    """Test handling of non-existent CSV file."""
    csv_file = tmp_path / "nonexistent.csv"

    processed_files, successful_rows = load_processed_talks_from_csv(csv_file)

    assert processed_files == set()
    assert successful_rows == []


def test_analyze_grace_works_balance_success(tmp_path: Path) -> None:
    """Test analyzing grace-works balance from CSV."""
    csv_file = tmp_path / "test.csv"

    # Create test CSV
    test_data = [
        ["conference_session_id", "score"],
        ["2024-04", "1"],
        ["2024-04", "2"],
        ["2024-10", "-1"],
        ["2024-10", "0"],
        ["invalid", "not_a_number"],  # Should be skipped
    ]

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(test_data)

    # This function prints to stdout, so we just verify it doesn't crash
    analyze_grace_works_balance(csv_file)


def test_analyze_grace_works_balance_file_not_found(tmp_path: Path) -> None:
    """Test handling of non-existent file for analysis."""
    csv_file = tmp_path / "nonexistent.csv"

    # Should not crash
    analyze_grace_works_balance(csv_file)


def test_analyze_grace_works_balance_missing_columns(tmp_path: Path) -> None:
    """Test handling of CSV with missing required columns."""
    csv_file = tmp_path / "test.csv"

    # Create CSV without required columns
    test_data = [
        ["filename", "other_column"],
        ["test1.html", "value"],
    ]

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(test_data)

    # Should not crash
    analyze_grace_works_balance(csv_file)
