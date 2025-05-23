"""
CSV management functions for the Conference Talk Grace-Works Classifier.

This module handles reading and writing CSV data with proper type hints.
"""

import csv
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

from models import ProcessingResult, TalkData


def write_to_csv(data: List[Dict[str, Any]], filename: Path, write_header: bool) -> None:
    """
    Writes the collected data to a CSV file, appending if write_header is False.

    Args:
        data: List of dictionaries containing talk data
        filename: Path to the CSV file
        write_header: Whether to write the header row
    """
    if not data:
        # This might happen if a batch is empty, though unlikely with current logic
        return

    output_dir = filename.parent
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

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

    file_mode = "w" if write_header else "a"

    with open(filename, file_mode, newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for row in data:
            writer.writerow(row)

    if write_header:  # Only print this message once for the file creation
        print(f"Data successfully written to {filename}")
    else:
        print(f"Appended {len(data)} talks to {filename}")


def load_processed_talks_from_csv(csv_filepath: Path) -> Tuple[Set[str], List[Dict[str, Any]]]:
    """
    Loads successfully processed talks from a given CSV file.

    Args:
        csv_filepath: Path to the CSV file

    Returns:
        A tuple: (set_of_processed_filenames, list_of_successful_rows_data)
        Returns (set(), []) if the file doesn't exist or an error occurs.
    """
    if not csv_filepath.exists():
        print(f"Resume CSV file not found: {csv_filepath}")
        return set(), []

    processed_filenames: Set[str] = set()
    successful_rows_data: List[Dict[str, Any]] = []
    error_indicators = ["Error parsing LLM response", "Error in classification"]

    try:
        with open(csv_filepath, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            for row in reader:
                filename = row.get("filename", "")
                explanation = row.get("explanation", "")

                # Skip rows with error indicators
                if any(error_text in explanation for error_text in error_indicators):
                    print(f"Skipping {filename} due to previous error: {explanation}")
                    continue

                processed_filenames.add(filename)
                successful_rows_data.append(row)

    except Exception as e:
        print(f"Error reading CSV file {csv_filepath}: {e}")
        return set(), []

    print(f"Loaded {len(processed_filenames)} successfully processed talks from {csv_filepath}")
    return processed_filenames, successful_rows_data


def analyze_grace_works_balance(csv_filepath: Path) -> None:
    """
    Analyzes grace-works balance from the CSV file and prints average scores per conference session.

    Args:
        csv_filepath: Path to the CSV file to analyze
    """
    if not csv_filepath.exists():
        print(f"Error: CSV file '{csv_filepath}' not found for analysis.")
        return

    conference_session_scores: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"total_score": 0, "count": 0}
    )

    try:
        with open(csv_filepath, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            if (
                not reader.fieldnames
                or "conference_session_id" not in reader.fieldnames
                or "score" not in reader.fieldnames
            ):
                print(
                    f"Error: CSV file must contain 'conference_session_id' and 'score' columns. Found: {reader.fieldnames}"
                )
                return

            for row in reader:
                try:
                    session_id = row["conference_session_id"]
                    score = int(row["score"])
                    conference_session_scores[session_id]["total_score"] += score
                    conference_session_scores[session_id]["count"] += 1
                except ValueError:
                    print(f"Skipping row due to invalid score: {row}")
                except KeyError:
                    print(f"Skipping row due to missing key: {row}")

    except Exception as e:
        print(f"Error reading or processing CSV file {csv_filepath}: {e}")
        return

    print("\n--- Grace-Works Balance Analysis ---")
    if not conference_session_scores:
        print("No data to analyze.")
        return

    print("Average Grace-Works Score per Conference Session (YYYY-MM):")
    sorted_sessions = sorted(conference_session_scores.items())

    plot_session_ids: List[str] = []
    plot_avg_scores: List[float] = []

    for session_id, data in sorted_sessions:
        if data["count"] > 0:
            avg_score = data["total_score"] / data["count"]
            print(f"- {session_id}: {avg_score:.2f} (from {data['count']} talks)")
            plot_session_ids.append(session_id)
            plot_avg_scores.append(avg_score)
        else:
            print(f"- {session_id}: No scores recorded")

    print("\nTo generate a line plot, you would typically use a library like Matplotlib:")
    print("Example using Matplotlib (ensure it's installed: pip install matplotlib):")
    print(
        """
import matplotlib.pyplot as plt
# Assuming 'plot_session_ids' list contains conference session identifiers (e.g., YYYY-MM)
# and 'plot_avg_scores' list contains the corresponding average scores.

plt.figure(figsize=(12, 6))
plt.plot(plot_session_ids, plot_avg_scores, marker='o', linestyle='-')
plt.xlabel("Conference Session (YYYY-MM)")
plt.ylabel("Average Grace-Works Score")
plt.title("Balance Between Grace and Works Over Time")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.grid(True)
plt.show()
"""
    )
