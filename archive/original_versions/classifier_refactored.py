#!/usr/bin/env python3
"""
Refactored Conference Talk Grace-Works Classifier.

This module provides a type-safe, modular approach to classifying conference talks
on a grace-works theological spectrum using OpenAI's API.
"""
import argparse
import json
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, Template
from openai import OpenAI

# Import our type-safe modules
from models import Classification, ClassifierConfig, TalkData, TalkMetadata
from processors.classifier_processor import get_llm_classification
from processors.csv_manager import (
    analyze_grace_works_balance,
    load_processed_talks_from_csv,
    write_to_csv,
)
from processors.file_processor import (
    extract_body_text_and_speaker,
    extract_metadata_from_filename,
    get_talk_files,
)

# Load environment variables
load_dotenv()


def create_classifier_config() -> ClassifierConfig:
    """Create and validate classifier configuration."""
    config = ClassifierConfig(
        talks_dir=Path("conference_talks"),
        output_dir=Path("output"),
        templates_dir=Path("templates"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "o4-mini-2025-04-16"),
    )

    # Validate configuration
    errors = config.validate()
    if errors:
        error_msg = "\n".join(f"- {error}" for error in errors)
        raise ValueError(f"Configuration errors:\n{error_msg}")

    return config


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Classify conference talks using OpenAI API.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--num-talks",
        type=int,
        help="Number of random talks to process (optional). Processes all if not set.",
    )

    parser.add_argument(
        "--file", type=str, help="Path to a single HTML file to process (optional)."
    )

    parser.add_argument(
        "--generate-batch-input",
        type=str,
        metavar="BATCH_FILEPATH",
        help="Generate a JSONL file for OpenAI batch processing instead of real-time classification.",
    )

    parser.add_argument(
        "--resume-from-csv",
        type=str,
        metavar="RESUME_CSV_PATH",
        help="Path to a previously generated CSV file. Only process talks not present in this CSV.",
    )

    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("OPENAI_MODEL", "o4-mini-2025-04-16"),
        help="Specify the OpenAI model to use.",
    )

    return parser.parse_args()


def setup_openai_and_template(config: ClassifierConfig) -> Tuple[OpenAI, Template]:
    """Initialize OpenAI client and Jinja template."""
    client = OpenAI(api_key=config.openai_api_key)

    env = Environment(loader=FileSystemLoader(config.templates_dir))
    template = env.get_template("classify_prompt.jinja")

    return client, template


def determine_files_to_process(
    config: ClassifierConfig, args: argparse.Namespace, processed_filenames: Set[str]
) -> List[Path]:
    """
    Determine which files need to be processed based on arguments and resume state.

    Args:
        config: Classifier configuration
        args: Parsed command line arguments
        processed_filenames: Set of already processed filenames

    Returns:
        List of file paths to process
    """
    if args.file:
        file_path = Path(args.file)
        if file_path.exists():
            if file_path.name not in processed_filenames:
                return [file_path]
            else:
                print(f"Skipping {args.file} as it was found in the resume CSV.")
                return []
        else:
            print(f"Error: File not found: {args.file}")
            return []

    # Get all available talk files
    all_talk_files = get_talk_files(config.talks_dir)

    if args.num_talks and args.num_talks < len(all_talk_files):
        # Filter out already processed talks BEFORE random sampling
        available_for_sampling = [f for f in all_talk_files if f.name not in processed_filenames]

        if args.num_talks > len(available_for_sampling):
            print(
                f"Warning: Requested {args.num_talks} talks, but only {len(available_for_sampling)} "
                f"are available after considering the resume CSV. Processing {len(available_for_sampling)}."
            )
            return available_for_sampling
        else:
            return random.sample(available_for_sampling, args.num_talks)
    else:
        return [f for f in all_talk_files if f.name not in processed_filenames]


def generate_batch_file(
    config: ClassifierConfig,
    args: argparse.Namespace,
    template: Template,
    batch_output_filepath: str,
) -> None:
    """Generate batch input file for OpenAI batch processing."""
    print(f"Generating batch input file: {batch_output_filepath}")

    # Determine files for batch processing
    if args.file:
        files_for_batch = [Path(args.file)]
    elif args.num_talks:
        all_files = get_talk_files(config.talks_dir)
        if args.num_talks <= len(all_files):
            files_for_batch = random.sample(all_files, args.num_talks)
        else:
            files_for_batch = all_files
    else:
        files_for_batch = get_talk_files(config.talks_dir)

    batch_requests = []

    for i, filepath in enumerate(files_for_batch):
        metadata = extract_metadata_from_filename(str(filepath), config.filename_pattern)
        if metadata is None:
            print(f"Skipping {filepath} due to filename parsing error.")
            continue

        content_result = extract_body_text_and_speaker(filepath)
        if not content_result.success or not content_result.data:
            print(f"Skipping {filepath} due to content extraction error.")
            continue

        talk_content = content_result.data["content"]

        if not talk_content.text_content:
            print(f"Skipping {filepath} due to missing content.")
            continue

        # Determine final speaker name
        final_speaker_name = (
            talk_content.speaker_name_from_html
            or metadata.speaker_name_from_filename
            or "Unknown Speaker"
        )

        metadata_dict = {
            "title": metadata.talk_identifier or filepath.name,
            "speaker": final_speaker_name,
            "year": metadata.year,
            "month": metadata.month,
            "conference": metadata.conference_session_id,
        }

        prompt = template.render(
            title=metadata_dict.get("title", "Unknown Title"),
            speaker=metadata_dict.get("speaker", "Unknown Speaker"),
            conference=metadata_dict.get("conference", "Unknown Conference"),
            date=f"{metadata_dict.get('year', '')}-{metadata_dict.get('month', '')}",
            content=talk_content.text_content,
        )

        batch_requests.append(
            {
                "custom_id": f"request_{i+1}_{filepath.name}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": args.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert at analyzing religious talks and determining their theological emphasis. You will output a JSON object with the fields 'score', 'explanation', and 'key_phrases'.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"},
                },
            }
        )

    try:
        with open(batch_output_filepath, "w") as f:
            for req in batch_requests:
                f.write(json.dumps(req) + "\n")
        print(f"Successfully wrote {len(batch_requests)} requests to {batch_output_filepath}")
    except IOError as e:
        print(f"Error writing batch input file: {e}")


def process_single_talk(
    filepath: Path, config: ClassifierConfig, template: Template, client: OpenAI, model: str
) -> Optional[Dict[str, Any]]:
    """
    Process a single talk file and return the talk data.

    Args:
        filepath: Path to the talk file
        config: Classifier configuration
        template: Jinja template for prompts
        client: OpenAI client
        model: Model name to use

    Returns:
        Dictionary containing talk data or None if processing failed
    """
    print(f"Processing file: {filepath}...")

    # Extract metadata from filename
    metadata = extract_metadata_from_filename(str(filepath), config.filename_pattern)
    if metadata is None:
        print(f"Skipping {filepath} due to filename metadata extraction error.")
        return None

    # Extract content from file
    content_result = extract_body_text_and_speaker(filepath)
    if not content_result.success or not content_result.data:
        print(f"Skipping {filepath} due to content extraction error.")
        return {
            "filename": filepath.name,
            "year": metadata.year,
            "month": metadata.month,
            "conference_session_id": metadata.conference_session_id,
            "talk_identifier": metadata.talk_identifier,
            "speaker_name": metadata.speaker_name_from_filename or "Unknown Speaker",
            "text_preview": "Error: Could not read content",
            "score": 0,
            "explanation": "File content extraction failed",
            "key_phrases": "",
            "model_used": model,
        }

    talk_content = content_result.data["content"]

    if not talk_content.text_content:
        print(f"Skipping {filepath} due to missing content.")
        return {
            "filename": filepath.name,
            "year": metadata.year,
            "month": metadata.month,
            "conference_session_id": metadata.conference_session_id,
            "talk_identifier": metadata.talk_identifier,
            "speaker_name": metadata.speaker_name_from_filename or "Unknown Speaker",
            "text_preview": "Error: Could not read content",
            "score": 0,
            "explanation": "File content extraction failed",
            "key_phrases": "",
            "model_used": model,
        }

    # Determine final speaker name
    final_speaker_name = (
        talk_content.speaker_name_from_html
        or metadata.speaker_name_from_filename
        or "Unknown Speaker"
    )

    # Create metadata dictionary for classification
    metadata_dict = {
        "title": metadata.talk_identifier or filepath.name,
        "speaker": final_speaker_name,
        "year": metadata.year,
        "month": metadata.month,
        "conference": metadata.conference_session_id,
    }

    print(
        f"Classifying talk: {metadata_dict.get('title')} by {metadata_dict.get('speaker')} using model {model}..."
    )

    # Get classification
    classification = get_llm_classification(
        talk_content.text_content, metadata_dict, template, client, model
    )

    # Create talk data dictionary
    talk_data = {
        "filename": filepath.name,
        "year": metadata.year,
        "month": metadata.month,
        "conference_session_id": metadata.conference_session_id,
        "talk_identifier": metadata.talk_identifier,
        "speaker_name": final_speaker_name,
        "text_preview": talk_content.text_content[: config.text_preview_length].replace("\n", " ")
        + "...",
        "score": classification.score,
        "explanation": classification.explanation,
        "key_phrases": ", ".join(classification.key_phrases),
        "model_used": model,
    }

    return talk_data


def process_talks_with_incremental_write(
    files_to_process: List[Path],
    config: ClassifierConfig,
    template: Template,
    client: OpenAI,
    model: str,
    output_csv_path: Path,
    has_resumed_data: bool,
) -> None:
    """
    Process talk files with incremental writing to CSV.

    Args:
        files_to_process: List of file paths to process
        config: Classifier configuration
        template: Jinja template for prompts
        client: OpenAI client
        model: Model name to use
        output_csv_path: Path to output CSV file
        has_resumed_data: Whether resumed data was already written
    """
    if not files_to_process:
        print("No talks to process.")
        return

    all_talks_data = []
    batch_size = config.batch_size

    print(f"\nProcessing {len(files_to_process)} talks...")

    for i, filepath in enumerate(files_to_process):
        talk_data = process_single_talk(filepath, config, template, client, model)

        if talk_data:
            all_talks_data.append(talk_data)

        # Incremental write logic
        if (i + 1) % batch_size == 0 or (i + 1) == len(files_to_process):
            # Determine if header is needed
            file_exists_and_has_content = (
                output_csv_path.exists() and output_csv_path.stat().st_size > 0
            )

            should_write_header = not file_exists_and_has_content

            if all_talks_data:  # Only write if we have data
                write_to_csv(all_talks_data, output_csv_path, should_write_header)
                all_talks_data = []  # Reset batch


def main() -> None:
    """Main function to orchestrate the talk processing pipeline."""
    try:
        # Setup
        config = create_classifier_config()
        args = parse_arguments()
        client, template = setup_openai_and_template(config)

        # Handle resume logic
        processed_filenames: Set[str] = set()
        resumed_data: List[Dict[str, Any]] = []

        if args.resume_from_csv:
            resume_csv_path = Path(args.resume_from_csv)
            processed_filenames, resumed_data = load_processed_talks_from_csv(resume_csv_path)
            print(
                f"Resuming from {args.resume_from_csv}. Found {len(processed_filenames)} already processed talks."
            )

        # Determine files to process
        files_to_process = determine_files_to_process(config, args, processed_filenames)

        # Create output file path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_csv_path = config.output_dir / f"conference_talk_scores_{timestamp}.csv"

        # Ensure output directory exists
        config.output_dir.mkdir(parents=True, exist_ok=True)

        # Write resumed data first if any
        if resumed_data:
            print(f"Writing {len(resumed_data)} resumed talks to {output_csv_path}...")
            write_to_csv(resumed_data, output_csv_path, write_header=True)

        # Handle batch generation mode
        if args.generate_batch_input:
            generate_batch_file(config, args, template, args.generate_batch_input)
            return

        # Check if there's anything to process
        if not files_to_process and not resumed_data:
            print("No new talks to process.")
            return

        # Process talks with incremental writing
        process_talks_with_incremental_write(
            files_to_process,
            config,
            template,
            client,
            args.model,
            output_csv_path,
            bool(resumed_data),
        )

        # Final output and analysis
        if output_csv_path.exists():
            print(f"\nAll processing complete. Final data saved to {output_csv_path}")
            analyze_grace_works_balance(output_csv_path)
        else:
            print("\nNo data was processed or written.")

    except Exception as e:
        print(f"Error: {e}")
        return


if __name__ == "__main__":
    main()
