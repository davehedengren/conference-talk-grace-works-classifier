import os
import pandas as pd
import argparse
from bs4 import BeautifulSoup
import re # Added for regex operations
from tqdm import tqdm # Added for progress bar

# --- Configuration ---
TALKS_DIR = "conference_talks"

def get_html_files(directory):
    """Gets a list of .html filenames (basenames) from the specified directory."""
    files = []
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' not found.")
        return files
    for filename in os.listdir(directory):
        if filename.endswith(".html") and not filename.startswith("."):
            files.append(filename)
    return files

def extract_speaker_from_html(filepath):
    """
    Extracts and cleans speaker name from the HTML file using BeautifulSoup.
    Looks for <p class=\"author-name\">.
    Cleans common prefixes (e.g., "By Elder/Sister") and special characters.
    Returns the cleaned speaker name string if found, otherwise None.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        speaker_tag = soup.find('p', class_='author-name')
        if speaker_tag:
            raw_speaker_text = speaker_tag.get_text(strip=False) # Get text with internal spaces

            cleaned_name = raw_speaker_text
            # 1. Specific character cleaning (e.g., Â and non-breaking space variants)
            cleaned_name = cleaned_name.replace('Â\\xa0', ' ') # Â followed by non-breaking space
            cleaned_name = cleaned_name.replace('Â ', ' ')    # Â followed by regular space
            cleaned_name = cleaned_name.replace('Â', '')       # Standalone Â

            # 2. Normalize general whitespace (multiple spaces to one, trim leading/trailing)
            cleaned_name = re.sub(r'\\s+', ' ', cleaned_name).strip()
            
            # 3. Remove prefixes (order matters: longest and most specific first)
            prefixes_to_remove = [
                "By President ", 
                "By Elder ", 
                "By Sister ", 
                "By " # General "By " should be last
            ]
            for prefix in prefixes_to_remove:
                if cleaned_name.startswith(prefix):
                    cleaned_name = cleaned_name[len(prefix):]
                    cleaned_name = cleaned_name.strip() # Re-strip after removing prefix
                    break # Assume only one such prefix is present
            
            return cleaned_name if cleaned_name else None # Return None if name becomes empty
            
        # If no <p class='author-name'>, try the original subtitle logic as a fallback if desired
        # For now, strictly adhering to author-name as per examples.
        # subtitle_p = soup.find('p', {'class': 'subtitle-LKtQp'})
        # if subtitle_p:
        #     return subtitle_p.text.strip()
        # subtitle_p = soup.find('p', {'class': 'subtitle'})
        # if subtitle_p:
        #     return subtitle_p.text.strip()
            
        return None # No suitable tag found
    except Exception as e:
        print(f"Error extracting speaker from {filepath}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Extracts speaker names from HTML files and joins them to an existing CSV.")
    parser.add_argument("--input-csv", required=True, help="Path to the input CSV file.")
    parser.add_argument("--output-csv", required=True, help="Path for the new output CSV file.")
    args = parser.parse_args()

    # 1. Get all HTML files and extract speaker names
    html_files = get_html_files(TALKS_DIR)
    if not html_files:
        print(f"No HTML files found in '{TALKS_DIR}'. Exiting.")
        return

    speaker_data = []
    print(f"Extracting speaker names from {len(html_files)} HTML files...")
    for fname_basename in tqdm(html_files, desc="Processing HTML files"):
        filepath = os.path.join(TALKS_DIR, fname_basename)
        speaker = extract_speaker_from_html(filepath)
        speaker_data.append({
            'filename': fname_basename,
            'speaker_name_from_html': speaker # Will be None if not found
        })
    
    if not speaker_data:
        print("No speaker data could be extracted from HTML files. Exiting.")
        return
        
    speakers_df = pd.DataFrame(speaker_data)

    # 2. Read the input CSV
    try:
        input_df = pd.read_csv(args.input_csv)
    except FileNotFoundError:
        print(f"Error: Input CSV file not found at '{args.input_csv}'.")
        return
    except Exception as e:
        print(f"Error reading input CSV file: {e}")
        return
        
    if 'filename' not in input_df.columns:
        print(f"Error: The input CSV must contain a 'filename' column for joining.")
        return

    # 3. Merge the input DataFrame with the speaker names DataFrame
    # Using a left merge to keep all rows from input_df
    merged_df = pd.merge(input_df, speakers_df, on='filename', how='left')
    
    # The 'speaker_name_from_html' column will have NaN where no speaker was extracted
    # or if the filename from the CSV wasn't in TALKS_DIR. pandas to_csv handles NaN as empty strings.

    # 4. Write to the new CSV file
    try:
        output_dir = os.path.dirname(args.output_csv)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        merged_df.to_csv(args.output_csv, index=False)
        print(f"Successfully created '{args.output_csv}' with speaker names from HTML files.")
    except Exception as e:
        print(f"Error writing output CSV file: {e}")

if __name__ == "__main__":
    main() 