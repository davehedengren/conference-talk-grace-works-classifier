import os
import csv
import random
import re
import json
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
import argparse # Added for command-line arguments
from datetime import datetime # Added for timestamping

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
TALKS_DIR = "conference_talks"
OUTPUT_DIR = "output"  # Define output directory
CSV_BASENAME = "conference_talk_scores" # Define base CSV filename
TEMPLATES_DIR = "templates"
# Regex to extract year, month, and a talk identifier from filename
# Assumes format: YYYY-MM-Identifier_anythingelse.html
FILENAME_PATTERN = re.compile(r"(\d{4})-(\d{2})-([^_]+)_.+\.html")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
if not os.getenv('OPENAI_API_KEY'):
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please create a .env file with your API key.")

# Initialize Jinja environment
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
template = env.get_template('classify_prompt.jinja')

# --- Helper Functions ---

def get_talk_files(directory):
    """Gets a list of .html files from the specified directory."""
    files = []
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' not found.")
        return files
    for filename in os.listdir(directory):
        if filename.endswith(".html") and not filename.startswith("."):
            files.append(os.path.join(directory, filename))
    return files

def extract_metadata_from_filename(filename):
    """Extracts year, month, and a talk identifier from the filename.
       The conference session for grouping will be YYYY-MM.
    """
    match = FILENAME_PATTERN.match(os.path.basename(filename))
    if match:
        year, month, talk_identifier = match.groups()
        conference_session_id = f"{year}-{month}" # For grouping
        return year, month, conference_session_id, talk_identifier
    print(f"Warning: Could not extract metadata from filename: {filename} (pattern: {FILENAME_PATTERN.pattern})")
    return None, None, None, None

def extract_body_text(filepath):
    """
    Extracts body text from HTML file using BeautifulSoup.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            # Get text and clean it up
            text = soup.get_text()
            # Break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return ""

def get_llm_classification(text_content, metadata):
    """
    Uses the Jinja template to generate a prompt for the LLM and processes its response.
    Makes an actual API call to OpenAI.
    """
    # Generate the prompt using the template
    prompt = template.render(
        title=metadata.get('title', 'Unknown Title'),
        speaker=metadata.get('speaker', 'Unknown Speaker'),
        conference=metadata.get('conference', 'Unknown Conference'),
        date=f"{metadata.get('year', '')}-{metadata.get('month', '')}",
        content=text_content
    )
    
    print(f"Generated prompt for talk: {metadata.get('title', 'Unknown Title')}")
    
    try:
        # Make the API call to OpenAI
        response = client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4.1-2025-04-14'),
            messages=[
                {"role": "system", "content": "You are an expert at analyzing religious talks and determining their theological emphasis. You will output a JSON object with the fields 'score', 'explanation', and 'key_phrases'."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,  # Lower temperature for more consistent classifications
            response_format={"type": "json_object"} # Enable JSON mode
        )
        
        # Extract the response content
        response_text = response.choices[0].message.content
        
        # Pre-processing for score format is no longer needed with JSON mode
        # response_text = response_text.replace('"score": +', '"score": ')

        # Parse the JSON response
        try:
            classification = json.loads(response_text)
            # Validate the response format
            if not all(key in classification for key in ['score', 'explanation', 'key_phrases']):
                raise ValueError("Response missing required fields")
            if not isinstance(classification['score'], int) or not -3 <= classification['score'] <= 3:
                raise ValueError("Score must be an integer between -3 and 3")
            return classification
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response as JSON: {e}")
            print(f"Raw response: {response_text}")
            return {
                "score": 0,
                "explanation": "Error parsing LLM response",
                "key_phrases": ["Error in classification"]
            }
            
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return {
            "score": 0,
            "explanation": f"Error in classification: {str(e)}",
            "key_phrases": ["Error in classification"]
        }

def write_to_csv(data, filename, write_header):
    """Writes the collected data to a CSV file, appending if write_header is False."""
    if not data:
        # This might happen if a batch is empty, though unlikely with current logic
        # print("No data in current batch to write to CSV.")
        return

    output_dir = os.path.dirname(filename)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    fieldnames = ['filename', 'year', 'month', 'conference_session_id', 'talk_identifier', 
                      'text_preview', 'score', 'explanation', 'key_phrases']
    
    file_mode = 'w' if write_header else 'a'
    
    with open(filename, file_mode, newline='', encoding='utf-8') as csvfile: 
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for row in data:
            writer.writerow(row)
    
    if write_header: # Only print this message once for the file creation
        print(f"Data successfully written to {filename}")
    else:
        print(f"Appended {len(data)} talks to {filename}")

def analyze_grace_works_balance(csv_filepath):
    """Analyzes grace-works balance from the CSV file and prints average scores per conference session."""
    if not os.path.exists(csv_filepath):
        print(f"Error: CSV file '{csv_filepath}' not found for analysis.")
        return

    conference_session_scores = defaultdict(lambda: {'total_score': 0, 'count': 0})

    try:
        with open(csv_filepath, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            if 'conference_session_id' not in reader.fieldnames or 'score' not in reader.fieldnames:
                print(f"Error: CSV file must contain 'conference_session_id' and 'score' columns. Found: {reader.fieldnames}")
                return
                
            for row in reader:
                try:
                    session_id = row['conference_session_id'] 
                    score = int(row['score'])
                    conference_session_scores[session_id]['total_score'] += score
                    conference_session_scores[session_id]['count'] += 1
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

    plot_session_ids = [] 
    plot_avg_scores = []

    for session_id, data in sorted_sessions:
        if data['count'] > 0:
            avg_score = data['total_score'] / data['count']
            print(f"- {session_id}: {avg_score:.2f} (from {data['count']} talks)")
            plot_session_ids.append(session_id)
            plot_avg_scores.append(avg_score)
        else:
            print(f"- {session_id}: No scores recorded")
    
    print("\nTo generate a line plot, you would typically use a library like Matplotlib:")
    print("Example using Matplotlib (ensure it's installed: pip install matplotlib):")
    print("""
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
""")

def load_processed_talks_from_csv(csv_filepath):
    """Loads successfully processed talks from a given CSV file.

    Returns:
        A tuple: (set_of_processed_filenames, list_of_successful_rows_data)
        Returns (set(), []) if the file doesn't exist or an error occurs.
    """
    if not os.path.exists(csv_filepath):
        print(f"Resume CSV file not found: {csv_filepath}")
        return set(), []

    processed_filenames = set()
    successful_rows_data = []
    error_indicators = ["Error parsing LLM response", "Error in classification"]

    try:
        with open(csv_filepath, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            if 'filename' not in reader.fieldnames or 'explanation' not in reader.fieldnames:
                print(f"Warning: Resume CSV {csv_filepath} is missing required 'filename' or 'explanation' columns. Cannot resume reliably.")
                return set(), []

            for row in reader:
                filename = row.get('filename')
                explanation = row.get('explanation', '')
                
                if not filename:
                    continue # Skip rows with no filename

                is_error = any(indicator in explanation for indicator in error_indicators)
                
                if not is_error and filename: # Assuming score presence implies some processing attempt
                    processed_filenames.add(filename)
                    successful_rows_data.append(row)
        print(f"Successfully loaded {len(successful_rows_data)} talks and {len(processed_filenames)} filenames from {csv_filepath}")
        return processed_filenames, successful_rows_data
    except Exception as e:
        print(f"Error reading or processing resume CSV file {csv_filepath}: {e}")
        return set(), []

# --- Main Execution ---

def main():
    """Main function to orchestrate the talk processing pipeline."""
    parser = argparse.ArgumentParser(description="Classify conference talks based on theological emphasis.")
    parser.add_argument(
        "--num-talks",
        type=int,
        default=None, # Process all talks by default
        help="Number of random talks to process. If not specified, all talks in TALKS_DIR will be processed."
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Path to a single talk file to process. Overrides --num-talks and processes only this file."
    )
    parser.add_argument(
        "--resume-from-csv",
        type=str,
        default=None,
        help="Path to a previously generated CSV file. Talks successfully processed in this CSV will not be re-processed, and their data will be carried to the new output CSV."
    )
    parser.add_argument(
        "--force-reclassify",
        action="store_true",
        help="Force re-classification of talks even if they exist in the output CSV. (Not yet implemented)" # Placeholder for future
    )
    args = parser.parse_args()

    # Generate timestamped output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = os.path.join(OUTPUT_DIR, f"{CSV_BASENAME}_{timestamp}.csv")

    print(f"Starting talk classification process...")
    print(f"Output CSV will be: {output_filename}")

    initial_data_from_resume_csv = []
    files_to_filter_out = set()

    if args.resume_from_csv:
        #  No need to check os.path.exists here, load_processed_talks_from_csv handles it
        print(f"Attempting to resume, loading data from: {args.resume_from_csv}")
        processed_filenames_set, existing_successful_rows = load_processed_talks_from_csv(args.resume_from_csv)
        if existing_successful_rows:
            initial_data_from_resume_csv.extend(existing_successful_rows)
            files_to_filter_out.update(processed_filenames_set)
    
    files_to_process_this_run = []
    if args.file: # Single file mode
        print(f"Processing single file specified: {args.file}")
        files_to_process_this_run = [args.file]
        file_being_processed_basename = os.path.basename(args.file)
        # Remove this specific file from initial_data_from_resume_csv to ensure it's re-processed by this run.
        initial_data_from_resume_csv = [row for row in initial_data_from_resume_csv if row.get('filename') != file_being_processed_basename]
        if file_being_processed_basename in files_to_filter_out:
             files_to_filter_out.remove(file_being_processed_basename)
    else: # Batch mode (all talks or --num-talks)
        print(f"Talks directory: {TALKS_DIR}")
        all_potential_files = get_talk_files(TALKS_DIR)
        if not all_potential_files:
            print(f"No .html files found in {TALKS_DIR}. Exiting.")
            return

        files_to_process_this_run = [f for f in all_potential_files if os.path.basename(f) not in files_to_filter_out]
        
        if args.num_talks is not None:
            if args.num_talks < len(files_to_process_this_run):
                print(f"Processing a random sample of {args.num_talks} talks from the remaining {len(files_to_process_this_run)} talks.")
                files_to_process_this_run = random.sample(files_to_process_this_run, args.num_talks)
            else:
                print(f"Requested {args.num_talks} talks, found {len(files_to_process_this_run)} remaining talks to process. Processing all remaining.")
        else:
             print(f"Processing all {len(files_to_process_this_run)} remaining talks after filtering.")

    if not files_to_process_this_run and not initial_data_from_resume_csv:
        print("No talks to process and no data to resume. Exiting.")
        return

    is_first_csv_write_for_new_file = True
    if initial_data_from_resume_csv:
        print(f"Writing {len(initial_data_from_resume_csv)} pre-existing successful talks to {output_filename}...")
        write_to_csv(initial_data_from_resume_csv, output_filename, write_header=True)
        is_first_csv_write_for_new_file = False

    talk_data_batch = []
    talks_processed_since_last_save = 0
    total_files_to_process_count = len(files_to_process_this_run)

    if total_files_to_process_count > 0:
        print(f"Starting processing of {total_files_to_process_count} talk(s) for this run...")
    else:
        print("No new talks to process in this run.")

    for index, filepath in enumerate(files_to_process_this_run):
        print(f"Processing talk {index + 1}/{total_files_to_process_count}: {os.path.basename(filepath)}")
        filename = os.path.basename(filepath)
        year, month, conf_session_id, talk_id = extract_metadata_from_filename(filename)
        
        if not conf_session_id:
            print(f"Skipping file {filename} due to missing metadata.")
            continue
            
        text_content = extract_body_text(filepath)
        if not text_content:
            print(f"Skipping file {filename} due to empty content.")
            continue

        # Create metadata dictionary for the template
        metadata = {
            'title': talk_id.replace('_', ' ').title(),
            'speaker': 'Unknown Speaker',  # TODO: Extract from HTML
            'conference': conf_session_id,
            'year': year,
            'month': month
        }

        classification = get_llm_classification(text_content, metadata)
        
        text_preview = (text_content.strip()[:75] + '...') if len(text_content.strip()) > 75 else text_content.strip()

        current_talk_data = {
            'filename': filename,
            'year': year,
            'month': month,
            'conference_session_id': conf_session_id,
            'talk_identifier': talk_id,
            'text_preview': text_preview.replace('\n', ' ').replace('\r', ' '),
            'score': classification['score'],
            'explanation': classification['explanation'],
            'key_phrases': ', '.join(classification['key_phrases'])
        }
        
        talk_data_batch.append(current_talk_data)
        talks_processed_since_last_save += 1

        # Check if it's time to write the batch to CSV
        if talks_processed_since_last_save >= 10 or (index + 1) == total_files_to_process_count:
            if talk_data_batch: # Ensure there's something to write
                print(f"Writing batch of {len(talk_data_batch)} talks to CSV...")
                write_to_csv(talk_data_batch, output_filename, write_header=is_first_csv_write_for_new_file)
                is_first_csv_write_for_new_file = False # Subsequent writes will append
                talk_data_batch = [] # Reset batch
                talks_processed_since_last_save = 0

    # The analyze_grace_works_balance function expects the file to be complete.
    # Check if any data was actually intended for the output file.
    if initial_data_from_resume_csv or total_files_to_process_count > 0:
        # Ensure the file exists and is not empty before analyzing, especially if only initial data was written and then no new talks.
        if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0: 
             analyze_grace_works_balance(output_filename)
        else:
            print(f"Output file {output_filename} is empty or does not exist. Skipping analysis.")
    else:
        print("No data was processed or collected. CSV and analysis will not be generated.")

if __name__ == "__main__":
    main() 