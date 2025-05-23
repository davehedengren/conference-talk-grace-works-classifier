#!/usr/bin/env python3
"""
Manages OpenAI Batch API interactions.

Usage:
  python batch_manager.py upload <filepath.jsonl>
  python batch_manager.py create <file_id> [--endpoint "/v1/chat/completions"] [--completion_window "24h"] [--metadata_desc "Batch job"]
  python batch_manager.py status <batch_id>
  python batch_manager.py list [--limit 10]
  python batch_manager.py download_results <batch_id> <output_filepath.jsonl>
"""
import argparse
import os
import time
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def upload_file(filepath):
    """Uploads a file for batch processing."""
    if not os.path.exists(filepath):
        print(f"Error: File not found at {filepath}")
        return
    try:
        with open(filepath, "rb") as f:
            batch_input_file = client.files.create(
                file=f,
                purpose="batch"
            )
        print(f"File uploaded successfully!")
        print(f"File ID: {batch_input_file.id}")
        print(f"Status: {batch_input_file.status}")
        print(f"Purpose: {batch_input_file.purpose}")
        return batch_input_file
    except Exception as e:
        print(f"Error uploading file: {e}")

def create_batch(file_id, endpoint, completion_window, metadata_desc):
    """Creates a new batch job."""
    try:
        batch_job = client.batches.create(
            input_file_id=file_id,
            endpoint=endpoint,
            completion_window=completion_window,
            metadata={
                "description": metadata_desc
            }
        )
        print(f"Batch job created successfully!")
        print(f"Batch ID: {batch_job.id}")
        print(f"Status: {batch_job.status}")
        # Add more details if needed
        return batch_job
    except Exception as e:
        print(f"Error creating batch job: {e}")

def get_batch_status(batch_id):
    """Retrieves the status of a batch job."""
    try:
        batch_job = client.batches.retrieve(batch_id)
        print(f"Batch ID: {batch_job.id}")
        print(f"Status: {batch_job.status}")
        print(f"Input File ID: {batch_job.input_file_id}")
        if batch_job.output_file_id:
            print(f"Output File ID: {batch_job.output_file_id}")
        if batch_job.error_file_id:
            print(f"Error File ID: {batch_job.error_file_id}")
        if batch_job.errors:
            print(f"Errors: {batch_job.errors}")
        # Add more details as available and useful
        return batch_job
    except Exception as e:
        print(f"Error retrieving batch status: {e}")

def list_batches(limit=10):
    """Lists recent batch jobs."""
    try:
        batches = client.batches.list(limit=limit)
        if not batches.data:
            print("No batch jobs found.")
            return
        print(f"Recent batch jobs (limit {limit}):")
        for batch in batches.data:
            print(f"- ID: {batch.id}, Status: {batch.status}, Created: {time.ctime(batch.created_at)}")
            if batch.metadata and batch.metadata.get('description'):
                print(f"  Description: {batch.metadata.get('description')}")
        return batches
    except Exception as e:
        print(f"Error listing batches: {e}")

def download_results(batch_id, output_filepath):
    """Downloads the results of a completed batch job."""
    try:
        batch_job = client.batches.retrieve(batch_id)
        if batch_job.status != 'completed':
            print(f"Batch job {batch_id} is not yet completed. Current status: {batch_job.status}")
            if batch_job.output_file_id:
                 print(f"Output file ID {batch_job.output_file_id} may exist but is not final.")
            return

        if not batch_job.output_file_id:
            print(f"Batch job {batch_id} is completed but has no output file ID.")
            return

        print(f"Downloading results from output file ID: {batch_job.output_file_id}")
        
        # Ensure the output directory exists
        output_dir = os.path.dirname(output_filepath)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")

        content = client.files.content(batch_job.output_file_id).read()
        with open(output_filepath, 'wb') as f: # Write as binary
            f.write(content)
        print(f"Results downloaded successfully to: {output_filepath}")

        # Optionally, you can also try to download the error file if it exists
        if batch_job.error_file_id:
            print(f"Attempting to download error file ID: {batch_job.error_file_id}")
            error_content = client.files.content(batch_job.error_file_id).read()
            error_filename = os.path.splitext(output_filepath)[0] + "_errors.jsonl"
            with open(error_filename, 'wb') as f_err:
                f_err.write(error_content)
            print(f"Error file downloaded to: {error_filename}")
            
    except Exception as e:
        print(f"Error downloading results: {e}")


def main():
    parser = argparse.ArgumentParser(description="Manage OpenAI Batch API jobs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload a file for batch processing.")
    upload_parser.add_argument("filepath", help="Path to the JSONL batch input file.")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new batch job.")
    create_parser.add_argument("file_id", help="ID of the uploaded batch input file.")
    create_parser.add_argument("--endpoint", default="/v1/chat/completions", help="API endpoint for the batch job.")
    create_parser.add_argument("--completion_window", default="24h", help="Completion window for the batch job.")
    create_parser.add_argument("--metadata_desc", default="Batch API Job", help="Description for batch metadata.")

    # Status command
    status_parser = subparsers.add_parser("status", help="Get the status of a batch job.")
    status_parser.add_argument("batch_id", help="ID of the batch job.")

    # List command
    list_parser = subparsers.add_parser("list", help="List recent batch jobs.")
    list_parser.add_argument("--limit", type=int, default=10, help="Number of jobs to list.")
    
    # Download results command
    download_parser = subparsers.add_parser("download_results", help="Download results of a completed batch job.")
    download_parser.add_argument("batch_id", help="ID of the completed batch job.")
    download_parser.add_argument("output_filepath", help="Filepath to save the downloaded results (e.g., results.jsonl).")

    args = parser.parse_args()

    if args.command == "upload":
        upload_file(args.filepath)
    elif args.command == "create":
        create_batch(args.file_id, args.endpoint, args.completion_window, args.metadata_desc)
    elif args.command == "status":
        get_batch_status(args.batch_id)
    elif args.command == "list":
        list_batches(args.limit)
    elif args.command == "download_results":
        download_results(args.batch_id, args.output_filepath)

if __name__ == "__main__":
    main() 