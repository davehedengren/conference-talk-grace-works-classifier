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
# Assumes format: YYYY-MM-Identifier_anythingelse.html or YYYY-MM-Identifier.html
# Updated to capture speaker name (alphanumeric) before the .html
FILENAME_PATTERN = re.compile(r"(\\d{4})-(\\d{2})-([^._]+)(?:_([a-zA-Z0-9]+))?\\.html")

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
       Also extracts speaker name if present in the format YYYY-MM-ID_SpeakerName.html.
    """
    match = FILENAME_PATTERN.match(os.path.basename(filename))
    if match:
        year, month, talk_identifier, speaker_from_filename = match.groups()
        conference_session_id = f"{year}-{month}" # For grouping
        # Speaker name from filename is a fallback
        return year, month, conference_session_id, talk_identifier, speaker_from_filename
    print(f"Warning: Could not extract metadata from filename: {filename} (pattern: {FILENAME_PATTERN.pattern})")
    return None, None, None, None, None

def extract_body_text_and_speaker(filepath):
    """
    Extracts body text and speaker name from HTML file using BeautifulSoup.
    Speaker name is looked for in <p class="author-name">.
    It also cleans common prefixes like "By Elder/Sister" and special characters.
    """
    speaker_name_from_html = None
    text_content = ""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Extract speaker name
            speaker_tag = soup.find('p', class_='author-name')
            if speaker_tag:
                raw_speaker_text = speaker_tag.get_text(strip=False) # Get text with spaces for better cleaning
                
                # Clean the speaker name
                cleaned_name = raw_speaker_text
                cleaned_name = cleaned_name.replace('Â\\xa0', ' ') # Replace Â and non-breaking space with a regular space
                cleaned_name = cleaned_name.replace('Â', '')     # Replace just Â if it exists
                
                # Remove prefixes - order matters here, longer ones first
                prefixes_to_remove = [
                    "By Elder ", "By Sister ", "By President ", "By "
                ]
                for prefix in prefixes_to_remove:
                    if cleaned_name.startswith(prefix):
                        cleaned_name = cleaned_name[len(prefix):]
                        break # Remove only the first matching prefix

                speaker_name_from_html = cleaned_name.strip()


            # Remove script and style elements for body text extraction
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()
            
            # Get text and clean it up
            text_content = soup.get_text()
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text_content = '\\n'.join(chunk for chunk in chunks if chunk)
            
            return text_content, speaker_name_from_html
    except Exception as e:
        print(f"Error reading or parsing file {filepath}: {e}")
        return "", None # Return empty text and None for speaker on error

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
            model=os.getenv('OPENAI_MODEL', 'o4-mini-2025-04-16'),
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
                  'speaker_name', 'text_preview', 'score', 'explanation', 'key_phrases', 'model_used']
    
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
    parser = argparse.ArgumentParser(description="Classify conference talks using OpenAI API.")
    parser.add_argument("--num-talks", type=int, help="Number of random talks to process (optional). Processes all if not set.")
    parser.add_argument("--file", type=str, help="Path to a single HTML file to process (optional).")
    parser.add_argument("--generate-batch-input", type=str, metavar="BATCH_FILEPATH",
                        help="Generate a JSONL file for OpenAI batch processing instead of real-time classification. Specify output filepath.")
    parser.add_argument("--resume-from-csv", type=str, metavar="RESUME_CSV_PATH",
                        help="Path to a previously generated CSV file. The script will only process talks not present in this CSV.")
    parser.add_argument("--model", type=str, default=os.getenv('OPENAI_MODEL', 'o4-mini-2025-04-16'),
                        help="Specify the OpenAI model to use (e.g., 'gpt-4.1-2025-04-14', 'o4-mini-2025-04-16'). Defaults to OPENAI_MODEL env var or 'o4-mini-2025-04-16'.")

    args = parser.parse_args()
    
    current_model_used = args.model

    talk_files_to_process = []
    processed_talk_filenames_from_resume = set()
    resumed_data_to_write = [] # Data from the resume CSV that needs to be carried over

    if args.resume_from_csv:
        processed_talk_filenames_from_resume, resumed_data_to_write = load_processed_talks_from_csv(args.resume_from_csv)
        print(f"Resuming from {args.resume_from_csv}. Found {len(processed_talk_filenames_from_resume)} already processed talks.")

    if args.file:
        if os.path.exists(args.file):
            if os.path.basename(args.file) not in processed_talk_filenames_from_resume:
                talk_files_to_process = [args.file]
            else:
                print(f"Skipping {args.file} as it was found in the resume CSV.")
        else:
            print(f"Error: File not found: {args.file}")
            return
    else:
        all_talk_files = get_talk_files(TALKS_DIR)
        if args.num_talks and args.num_talks < len(all_talk_files):
            # Filter out already processed talks BEFORE random sampling
            available_for_sampling = [f for f in all_talk_files if os.path.basename(f) not in processed_talk_filenames_from_resume]
            if args.num_talks > len(available_for_sampling):
                print(f"Warning: Requested {args.num_talks} talks, but only {len(available_for_sampling)} are available after considering the resume CSV. Processing {len(available_for_sampling)}.")
                talk_files_to_process = available_for_sampling
            else:
                talk_files_to_process = random.sample(available_for_sampling, args.num_talks)
        else:
            talk_files_to_process = [f for f in all_talk_files if os.path.basename(f) not in processed_talk_filenames_from_resume]

    if not talk_files_to_process and not args.generate_batch_input : # if generate_batch_input, we might still want an empty file
        if not resumed_data_to_write: # No new talks and no resumed talks means nothing to do/write
             print("No new talks to process.")
             return
        # If there's resumed data but no new talks, we still need to write the resumed data.

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv_filename = os.path.join(OUTPUT_DIR, f"{CSV_BASENAME}_{timestamp}.csv")
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # If resuming, write the old data first to the new timestamped file
    if resumed_data_to_write:
        # Ensure fieldnames in resumed_data_to_write match the current FIELDNAMES
        # This step might require careful handling if fieldnames change across versions
        # For now, assume they are compatible or that load_processed_talks_from_csv handles this.
        # The `load_processed_talks_from_csv` function now returns dicts, so it should be fine.
        print(f"Writing {len(resumed_data_to_write)} resumed talks to {output_csv_filename}...")
        write_to_csv(resumed_data_to_write, output_csv_filename, write_header=True)


    if args.generate_batch_input:
        batch_output_filepath = args.generate_batch_input
        print(f"Generating batch input file: {batch_output_filepath}")
        # If talk_files_to_process is empty because of resume, use all files for batch generation
        # as batch typically processes everything from scratch.
        # However, if the user explicitly provided --num-talks, respect that.
        files_for_batch = []
        if args.file: # Single file for batch
            files_for_batch = [args.file]
        elif args.num_talks: # Specific number for batch
             all_files = get_talk_files(TALKS_DIR)
             if args.num_talks <= len(all_files):
                files_for_batch = random.sample(all_files, args.num_talks)
             else:
                files_for_batch = all_files # Not enough, take all
        else: # All talks for batch
            files_for_batch = get_talk_files(TALKS_DIR)

        batch_requests = []
        for i, filepath in enumerate(files_for_batch):
            year, month, conference_session_id, talk_identifier, speaker_name_fn = extract_metadata_from_filename(filepath)
            text_content, speaker_name_html = extract_body_text_and_speaker(filepath)
            
            final_speaker_name = speaker_name_html if speaker_name_html else speaker_name_fn
            if not final_speaker_name:
                final_speaker_name = "Unknown Speaker"


            if not text_content:
                print(f"Skipping {filepath} due to missing content.")
                continue

            metadata = {
                "title": talk_identifier if talk_identifier else os.path.basename(filepath),
                "speaker": final_speaker_name,
                "year": year,
                "month": month,
                "conference": conference_session_id # Example, adjust as needed
            }
            prompt = template.render(
                title=metadata.get('title', 'Unknown Title'),
                speaker=metadata.get('speaker', 'Unknown Speaker'),
                conference=metadata.get('conference', 'Unknown Conference'),
                date=f"{metadata.get('year', '')}-{metadata.get('month', '')}",
                content=text_content
            )
            batch_requests.append({
                "custom_id": f"request_{i+1}_{os.path.basename(filepath)}", # Unique ID for each request
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": current_model_used, # Use the specified model
                    "messages": [
                        {"role": "system", "content": "You are an expert at analyzing religious talks and determining their theological emphasis. You will output a JSON object with the fields 'score', 'explanation',and 'key_phrases'."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"}
                }
            })
        
        try:
            with open(batch_output_filepath, 'w') as f:
                for req in batch_requests:
                    f.write(json.dumps(req) + '\n')
            print(f"Successfully wrote {len(batch_requests)} requests to {batch_output_filepath}")
        except IOError as e:
            print(f"Error writing batch input file: {e}")
        return # Exit after generating batch file

    if not talk_files_to_process:
        if not resumed_data_to_write: # Double check if there really is nothing to do.
             print("No talks to process and no resumed data to write.")
        else:
             print(f"All talks processed. Final data saved to {output_csv_filename}")
        return

    all_talks_data = [] # For newly processed talks in this run
    BATCH_SIZE_FOR_INCREMENTAL_WRITE = 10

    print(f"\nProcessing {len(talk_files_to_process)} talks...")

    for i, filepath in enumerate(talk_files_to_process):
        print(f"\nProcessing file ({i+1}/{len(talk_files_to_process)}): {filepath}...")
        
        year, month, conference_session_id, talk_identifier, speaker_name_fn = extract_metadata_from_filename(filepath)
        
        if year is None: # Error in filename parsing
            print(f"Skipping {filepath} due to filename metadata extraction error.")
            continue

        text_content, speaker_name_html = extract_body_text_and_speaker(filepath)
        final_speaker_name = speaker_name_html if speaker_name_html else speaker_name_fn
        if not final_speaker_name:
            final_speaker_name = "Unknown Speaker" # Default if neither method works

        if not text_content:
            print(f"Skipping {filepath} due to missing content.")
            # Optionally, write a row with an error message for this file
            talk_data = {
                'filename': os.path.basename(filepath),
                'year': year,
                'month': month,
                'conference_session_id': conference_session_id,
                'talk_identifier': talk_identifier,
                'speaker_name': final_speaker_name,
                'text_preview': "Error: Could not read content",
                'score': 0, # Or a specific error code/string
                'explanation': "File content extraction failed",
                'key_phrases': [],
                'model_used': current_model_used
            }
            all_talks_data.append(talk_data)
            # Incremental write logic
            if (i + 1) % BATCH_SIZE_FOR_INCREMENTAL_WRITE == 0:
                write_to_csv(all_talks_data, output_csv_filename, write_header=(not os.path.exists(output_csv_filename) or os.path.getsize(output_csv_filename) == 0) and not resumed_data_to_write) # Write header only if file is new AND no resumed data was written
                all_talks_data = [] # Reset batch
            continue

        metadata = {
            "title": talk_identifier if talk_identifier else os.path.basename(filepath),
            "speaker": final_speaker_name,
            "year": year,
            "month": month,
            "conference": conference_session_id # Example, adjust as needed
        }

        print(f"Classifying talk: {metadata.get('title')} by {metadata.get('speaker')} ({filepath}) using model {current_model_used}...")
        classification = get_llm_classification(text_content, metadata)

        talk_data = {
            'filename': os.path.basename(filepath),
            'year': year,
            'month': month,
            'conference_session_id': conference_session_id,
            'talk_identifier': talk_identifier,
            'speaker_name': final_speaker_name,
            'text_preview': text_content[:100].replace('\n', ' ') + "...", # First 100 chars as preview
            'score': classification.get('score', 0), # Default to 0 if missing
            'explanation': classification.get('explanation', 'N/A'),
            'key_phrases': ", ".join(classification.get('key_phrases', [])), # Convert list to comma-separated string
            'model_used': current_model_used
        }
        all_talks_data.append(talk_data)

        # Incremental write logic
        # Write header if:
        # 1. It's the first batch of this run (i < BATCH_SIZE_FOR_INCREMENTAL_WRITE implies it is, for the first write)
        # 2. The output file does not exist OR is empty
        # 3. No resumed data has been previously written to this file (which would have included a header)
        if (i + 1) % BATCH_SIZE_FOR_INCREMENTAL_WRITE == 0:
            # Header logic: write header if the file doesn't exist yet, or if it exists but is empty,
            # AND no resumed data has been written (which would have already laid down the header).
            is_first_write_to_this_file = (not os.path.exists(output_csv_filename) or os.path.getsize(output_csv_filename) == 0)
            header_needed = is_first_write_to_this_file and not resumed_data_to_write

            # If resumed_data_to_write was present, it means headers were written.
            # Subsequent writes should append.
            # If resumed_data_to_write was NOT present, then the very first write needs a header.

            should_write_header_for_this_batch = False
            if not resumed_data_to_write: # If we are not resuming, the first batch needs a header
                if i < BATCH_SIZE_FOR_INCREMENTAL_WRITE: # This is the first batch
                     should_write_header_for_this_batch = True
            # If we ARE resuming, resumed_data_to_write handled the header. All subsequent writes are appends.
            # This also implies that if resumed_data_to_write was empty, this logic path means it's effectively not resuming.

            current_file_exists_and_has_content = os.path.exists(output_csv_filename) and os.path.getsize(output_csv_filename) > 0
            
            final_header_decision = False
            if not current_file_exists_and_has_content: # File is new or empty
                final_header_decision = True
            # If file exists and has content, header is already there (either from resume or previous batch)
            
            write_to_csv(all_talks_data, output_csv_filename, write_header=final_header_decision)
            all_talks_data = [] # Reset batch for next set of talks

    # Write any remaining talks that didn't make up a full batch
    if all_talks_data:
        # Similar header logic for the final write
        current_file_exists_and_has_content = os.path.exists(output_csv_filename) and os.path.getsize(output_csv_filename) > 0
        final_header_decision = False
        if not current_file_exists_and_has_content:
            final_header_decision = True
            
        write_to_csv(all_talks_data, output_csv_filename, write_header=final_header_decision)

    if os.path.exists(output_csv_filename): # Check if file was actually created
         print(f"\nAll processing complete. Final data saved to {output_csv_filename}")
         analyze_grace_works_balance(output_csv_filename) # Optional: run analysis at the end
    elif not args.generate_batch_input: # Don't print if we only generated batch input
         print("\nNo data was processed or written.")


if __name__ == "__main__":
    main() 