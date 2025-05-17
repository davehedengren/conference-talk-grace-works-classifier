import os

TALKS_DIR = "conference_talks"
SUFFIX_TO_CHECK = "_lang=eng.html"
SIMPLE_SUFFIX = ".html"

def find_and_remove_duplicates():
    """
    Scans the TALKS_DIR for files ending with SUFFIX_TO_CHECK.
    If a corresponding file without the '_lang=eng' part exists,
    the simpler version (without '_lang=eng') is deleted.
    """
    if not os.path.exists(TALKS_DIR):
        print(f"Error: Directory '{TALKS_DIR}' not found.")
        return

    files_in_dir = os.listdir(TALKS_DIR)
    html_files = {f for f in files_in_dir if f.endswith(SIMPLE_SUFFIX)} # Set for efficient lookup

    files_deleted_count = 0
    potential_duplicates_found = 0

    for filename_with_lang in html_files:
        if filename_with_lang.endswith(SUFFIX_TO_CHECK):
            potential_duplicates_found += 1
            # Construct the base name and the potential simpler duplicate
            # Example: "my-talk_lang=eng.html" -> "my-talk"
            base_name_part = filename_with_lang[:-len(SUFFIX_TO_CHECK)]
            
            # Potential simpler duplicate: "my-talk.html"
            simpler_filename = base_name_part + SIMPLE_SUFFIX
            
            if simpler_filename in html_files and simpler_filename != filename_with_lang:
                simpler_filepath = os.path.join(TALKS_DIR, simpler_filename)
                try:
                    os.remove(simpler_filepath)
                    print(f"Deleted duplicate: {simpler_filepath} (kept {filename_with_lang})")
                    files_deleted_count += 1
                except OSError as e:
                    print(f"Error deleting file {simpler_filepath}: {e}")
            elif simpler_filename == filename_with_lang:
                # This case should not happen if logic is correct, but good to note.
                print(f"Warning: Filename with lang is identical to simpler filename construction for {filename_with_lang}")


    if potential_duplicates_found == 0:
        print(f"No files ending with '{SUFFIX_TO_CHECK}' found in '{TALKS_DIR}'.")
    elif files_deleted_count == 0 :
        print(f"Found {potential_duplicates_found} files ending with '{SUFFIX_TO_CHECK}', but no simpler duplicates (e.g., 'name.html') were found to remove.")
    else:
        print(f"\nScan complete. Deleted {files_deleted_count} duplicate files.")

if __name__ == "__main__":
    find_and_remove_duplicates() 