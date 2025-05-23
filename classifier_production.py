#!/usr/bin/env python3
"""
Production-ready Conference Talk Grace-Works Classifier with Structured Logging.

This module provides a high-performance, type-safe approach to classifying conference talks
with structured logging, progress tracking, caching, and comprehensive error handling.
"""
import argparse
import json
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, Template
from openai import OpenAI
from tqdm import tqdm

# Import our type-safe modules
from models import ClassifierConfig, Classification, TalkData, TalkMetadata
from processors.classifier_processor import get_llm_classification
from processors.csv_manager import analyze_grace_works_balance, load_processed_talks_from_csv, write_to_csv
from processors.file_processor import (
    extract_body_text_and_speaker,
    extract_metadata_from_filename,
    get_talk_files,
)
from utils.exceptions import (
    ClassificationError,
    ConfigurationError,
    FileProcessingError,
    TemplateError,
)
from utils.logging_config import LogContext, configure_classifier_logging, get_logger, log_performance

# Load environment variables
load_dotenv()

# Configure structured logging
logger = get_logger("classifier.production")


class ClassificationCache:
    """Simple in-memory cache for classification results to avoid re-processing."""

    def __init__(self) -> None:
        self._cache: Dict[str, Classification] = {}

    def get(self, content_hash: str) -> Optional[Classification]:
        """Get cached classification result."""
        return self._cache.get(content_hash)

    def set(self, content_hash: str, classification: Classification) -> None:
        """Cache classification result."""
        self._cache[content_hash] = classification

    def size(self) -> int:
        """Get cache size."""
        return len(self._cache)


@log_performance(logger, "configuration_creation")
def create_classifier_config() -> ClassifierConfig:
    """Create and validate classifier configuration."""
    try:
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
            logger.error("Configuration validation failed", errors=errors, error_count=len(errors))
            raise ConfigurationError(f"Configuration errors:\n{error_msg}")

        logger.info(
            "Configuration created successfully",
            talks_dir=str(config.talks_dir),
            output_dir=str(config.output_dir),
            model=config.openai_model,
        )
        return config

    except Exception as e:
        logger.error("Failed to create configuration", error=str(e), error_type=type(e).__name__)
        raise


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Production-ready classifier for conference talks using OpenAI API.",
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

    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bars (useful for logging/automation).",
    )

    parser.add_argument(
        "--rate-limit",
        type=float,
        default=0.1,
        help="Minimum seconds between API calls to respect rate limits.",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level.",
    )

    parser.add_argument(
        "--log-json", action="store_true", help="Output logs in JSON format for structured logging."
    )

    args = parser.parse_args()

    # Log parsed arguments
    logger.info(
        "Command line arguments parsed",
        num_talks=args.num_talks,
        single_file=args.file,
        batch_mode=bool(args.generate_batch_input),
        resume_mode=bool(args.resume_from_csv),
        model=args.model,
        rate_limit=args.rate_limit,
        log_level=args.log_level,
    )

    return args


@log_performance(logger, "openai_template_setup")
def setup_openai_and_template(config: ClassifierConfig) -> Tuple[OpenAI, Template]:
    """Initialize OpenAI client and Jinja template."""
    try:
        client = OpenAI(api_key=config.openai_api_key)

        if not config.templates_dir.exists():
            raise TemplateError(
                f"Templates directory not found: {config.templates_dir}",
                template_path=str(config.templates_dir),
            )

        env = Environment(loader=FileSystemLoader(config.templates_dir))
        template = env.get_template("classify_prompt.jinja")

        logger.info(
            "OpenAI client and template initialized",
            template_dir=str(config.templates_dir),
            template_name="classify_prompt.jinja",
        )

        return client, template

    except Exception as e:
        logger.error(
            "Failed to setup OpenAI client or template",
            error=str(e),
            error_type=type(e).__name__,
            template_dir=str(config.templates_dir),
        )
        raise


@log_performance(logger, "file_discovery")
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
    with LogContext(logger, operation="file_discovery") as log:
        if args.file:
            file_path = Path(args.file)
            if file_path.exists():
                if file_path.name not in processed_filenames:
                    log.info("Single file mode", filepath=str(file_path))
                    return [file_path]
                else:
                    log.warning("File already processed, skipping", filepath=str(file_path))
                    return []
            else:
                log.error("File not found", filepath=str(file_path))
                raise FileProcessingError(f"File not found: {file_path}", str(file_path), "read")

        # Get all available talk files
        log.info("Scanning for talk files", talks_dir=str(config.talks_dir))
        all_talk_files = get_talk_files(config.talks_dir)
        log.info("Talk files discovered", total_files=len(all_talk_files))

        if args.num_talks and args.num_talks < len(all_talk_files):
            # Filter out already processed talks BEFORE random sampling
            available_for_sampling = [f for f in all_talk_files if f.name not in processed_filenames]

            if args.num_talks > len(available_for_sampling):
                log.warning(
                    "Insufficient unprocessed files for requested sample size",
                    requested=args.num_talks,
                    available=len(available_for_sampling),
                    total_files=len(all_talk_files),
                    processed_files=len(processed_filenames),
                )
                return available_for_sampling
            else:
                selected = random.sample(available_for_sampling, args.num_talks)
                log.info("Random sample selected", selected_count=len(selected), requested=args.num_talks)
                return selected
        else:
            unprocessed = [f for f in all_talk_files if f.name not in processed_filenames]
            log.info(
                "Processing all unprocessed files",
                unprocessed_count=len(unprocessed),
                total_files=len(all_talk_files),
                already_processed=len(processed_filenames),
            )
            return unprocessed


@log_performance(logger, "batch_file_generation")
def generate_batch_file_optimized(
    config: ClassifierConfig, args: argparse.Namespace, template: Template, batch_output_filepath: str
) -> None:
    """Generate batch input file for OpenAI batch processing with progress tracking."""
    with LogContext(logger, operation="batch_generation", output_file=batch_output_filepath) as log:
        log.info("Starting batch file generation")

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

        # Use progress bar for batch generation
        progress_desc = "Generating batch requests"
        if args.no_progress:
            iterator = files_for_batch
            log.info("Progress disabled, processing files", file_count=len(files_for_batch))
        else:
            iterator = tqdm(files_for_batch, desc=progress_desc, unit="file")

        for i, filepath in enumerate(iterator):
            try:
                metadata = extract_metadata_from_filename(str(filepath), config.filename_pattern)
                if metadata is None:
                    log.warning("Skipping file due to metadata extraction failure", filepath=str(filepath))
                    continue

                content_result = extract_body_text_and_speaker(filepath)
                if not content_result.success or not content_result.data:
                    log.warning("Skipping file due to content extraction failure", filepath=str(filepath))
                    continue

                talk_content = content_result.data["content"]

                if not talk_content.text_content:
                    log.warning("Skipping file due to empty content", filepath=str(filepath))
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

            except Exception as e:
                log.error(
                    "Error processing file for batch",
                    filepath=str(filepath),
                    error=str(e),
                    error_type=type(e).__name__,
                )
                continue

        try:
            log.info("Writing batch requests to file", request_count=len(batch_requests))
            with open(batch_output_filepath, "w") as f:
                for req in batch_requests:
                    f.write(json.dumps(req) + "\n")

            log.info(
                "Batch file generation completed successfully",
                output_file=batch_output_filepath,
                requests_written=len(batch_requests),
                total_files_processed=len(files_for_batch),
            )

        except IOError as e:
            log.error("Failed to write batch input file", error=str(e), output_file=batch_output_filepath)
            raise


def process_single_talk_optimized(
    filepath: Path,
    config: ClassifierConfig,
    template: Template,
    client: OpenAI,
    model: str,
    cache: ClassificationCache,
    rate_limit: float = 0.1,
) -> Optional[Dict[str, Any]]:
    """
    Process a single talk file with caching and rate limiting.

    Args:
        filepath: Path to the talk file
        config: Classifier configuration
        template: Jinja template for prompts
        client: OpenAI client
        model: Model name to use
        cache: Classification cache
        rate_limit: Minimum seconds between API calls

    Returns:
        Dictionary containing talk data or None if processing failed
    """
    with LogContext(logger, operation="single_talk_processing", filepath=str(filepath)) as log:
        try:
            # Extract metadata from filename
            metadata = extract_metadata_from_filename(str(filepath), config.filename_pattern)
            if metadata is None:
                log.warning("Metadata extraction failed")
                return None

            # Extract content from file
            content_result = extract_body_text_and_speaker(filepath)
            if not content_result.success or not content_result.data:
                log.warning("Content extraction failed")
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
                log.warning("Empty content extracted")
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

            # Check cache first (using a simple hash of content)
            content_hash = str(hash(talk_content.text_content[:1000]))  # Hash first 1000 chars
            cached_classification = cache.get(content_hash)

            if cached_classification:
                log.debug("Using cached classification", content_hash=content_hash)
                classification = cached_classification
            else:
                # Rate limiting
                if rate_limit > 0:
                    time.sleep(rate_limit)

                # Get classification from API
                log.debug("Requesting new classification from API", content_length=len(talk_content.text_content))
                classification = get_llm_classification(talk_content.text_content, metadata_dict, template, client, model)

                # Cache the result
                cache.set(content_hash, classification)
                log.debug("Classification cached", content_hash=content_hash)

            # Create talk data dictionary
            talk_data = {
                "filename": filepath.name,
                "year": metadata.year,
                "month": metadata.month,
                "conference_session_id": metadata.conference_session_id,
                "talk_identifier": metadata.talk_identifier,
                "speaker_name": final_speaker_name,
                "text_preview": talk_content.text_content[: config.text_preview_length].replace("\n", " ") + "...",
                "score": classification.score,
                "explanation": classification.explanation,
                "key_phrases": ", ".join(classification.key_phrases),
                "model_used": model,
            }

            log.debug(
                "Talk processing completed",
                score=classification.score,
                speaker=final_speaker_name,
                content_length=len(talk_content.text_content),
            )

            return talk_data

        except Exception as e:
            log.error("Talk processing failed", error=str(e), error_type=type(e).__name__)
            raise


@log_performance(logger, "bulk_talk_processing")
def process_talks_with_progress(
    files_to_process: List[Path],
    config: ClassifierConfig,
    template: Template,
    client: OpenAI,
    model: str,
    output_csv_path: Path,
    has_resumed_data: bool,
    show_progress: bool = True,
    rate_limit: float = 0.1,
) -> None:
    """
    Process talk files with progress tracking and optimizations.

    Args:
        files_to_process: List of file paths to process
        config: Classifier configuration
        template: Jinja template for prompts
        client: OpenAI client
        model: Model name to use
        output_csv_path: Path to output CSV file
        has_resumed_data: Whether resumed data was already written
        show_progress: Whether to show progress bars
        rate_limit: Minimum seconds between API calls
    """
    with LogContext(
        logger,
        operation="bulk_processing",
        file_count=len(files_to_process),
        output_path=str(output_csv_path),
        model=model,
    ) as log:
        if not files_to_process:
            log.info("No talks to process")
            return

        cache = ClassificationCache()
        all_talks_data = []
        batch_size = config.batch_size

        log.info("Starting bulk processing", file_count=len(files_to_process), model=model)
        if rate_limit > 0:
            estimated_time = len(files_to_process) * rate_limit / 60
            log.info("Rate limiting enabled", rate_limit=rate_limit, estimated_time_minutes=round(estimated_time, 1))

        # Setup progress bar
        if show_progress:
            progress_bar = tqdm(
                files_to_process,
                desc="Classifying talks",
                unit="talk",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
            )
        else:
            progress_bar = files_to_process

        successful_classifications = 0
        failed_classifications = 0

        for i, filepath in enumerate(progress_bar):
            try:
                talk_data = process_single_talk_optimized(filepath, config, template, client, model, cache, rate_limit)

                if talk_data:
                    all_talks_data.append(talk_data)
                    if talk_data["score"] != 0 or "Error" not in talk_data["explanation"]:
                        successful_classifications += 1
                    else:
                        failed_classifications += 1

                    # Update progress bar with stats
                    if show_progress:
                        progress_bar.set_postfix(
                            {"success": successful_classifications, "failed": failed_classifications, "cache": cache.size()}
                        )

                # Incremental write logic
                if (i + 1) % batch_size == 0 or (i + 1) == len(files_to_process):
                    # Determine if header is needed
                    file_exists_and_has_content = output_csv_path.exists() and output_csv_path.stat().st_size > 0

                    should_write_header = not file_exists_and_has_content

                    if all_talks_data:  # Only write if we have data
                        write_to_csv(all_talks_data, output_csv_path, should_write_header)
                        log.debug("Incremental write completed", batch_size=len(all_talks_data), batch_number=(i + 1) // batch_size)
                        all_talks_data = []  # Reset batch

            except Exception as e:
                failed_classifications += 1
                log.error("File processing failed", filepath=str(filepath), error=str(e), error_type=type(e).__name__)
                continue

        log.info(
            "Bulk processing completed",
            successful=successful_classifications,
            failed=failed_classifications,
            cache_hits=cache.size(),
            total_processed=successful_classifications + failed_classifications,
        )


def main() -> None:
    """Main function with optimizations and structured logging."""
    try:
        # Parse arguments first to set up logging level
        args = parse_arguments()

        # Reconfigure logging with user-specified level
        if args.log_level or args.log_json:
            global logger
            logger = configure_classifier_logging(args.log_level, log_file=True, json_format=args.log_json)

        with LogContext(logger, operation="main_execution", version="1.0.0") as log:
            log.info("Starting Conference Talk Grace-Works Classifier", version="production-v1.0.0", model=args.model)

            # Setup
            config = create_classifier_config()
            client, template = setup_openai_and_template(config)

            # Handle resume logic
            processed_filenames: Set[str] = set()
            resumed_data: List[Dict[str, Any]] = []

            if args.resume_from_csv:
                log.info("Loading resume data", resume_file=args.resume_from_csv)
                resume_csv_path = Path(args.resume_from_csv)
                processed_filenames, resumed_data = load_processed_talks_from_csv(resume_csv_path)
                log.info("Resume data loaded", processed_count=len(processed_filenames), resumed_records=len(resumed_data))

            # Determine files to process
            files_to_process = determine_files_to_process(config, args, processed_filenames)

            # Create output file path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_csv_path = config.output_dir / f"conference_talk_scores_{timestamp}.csv"

            # Ensure output directory exists
            config.output_dir.mkdir(parents=True, exist_ok=True)

            # Write resumed data first if any
            if resumed_data:
                log.info("Writing resumed data", record_count=len(resumed_data), output_file=str(output_csv_path))
                write_to_csv(resumed_data, output_csv_path, write_header=True)

            # Handle batch generation mode
            if args.generate_batch_input:
                generate_batch_file_optimized(config, args, template, args.generate_batch_input)
                return

            # Check if there's anything to process
            if not files_to_process and not resumed_data:
                log.warning("No new talks to process")
                return

            # Process talks with optimizations
            process_talks_with_progress(
                files_to_process,
                config,
                template,
                client,
                args.model,
                output_csv_path,
                bool(resumed_data),
                show_progress=not args.no_progress,
                rate_limit=args.rate_limit,
            )

            # Final output and analysis
            if output_csv_path.exists():
                log.info("Processing completed successfully", output_file=str(output_csv_path))
                analyze_grace_works_balance(output_csv_path)
            else:
                log.warning("No data was processed or written")

    except KeyboardInterrupt:
        logger.warning("Processing interrupted by user")
    except Exception as e:
        logger.error("Application error", error=str(e), error_type=type(e).__name__, exc_info=True)
        return


if __name__ == "__main__":
    main() 