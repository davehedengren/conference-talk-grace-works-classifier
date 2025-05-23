import pandas as pd
import re
from itertools import combinations
from thefuzz import fuzz # Corrected import: For fuzzy matching

# Configuration
INPUT_CSV_PATH = 'output/labeled_conference_talks_with_speaker_names_20250520.csv' # Or your latest raw output
OUTPUT_CSV_PATH = 'output/cleaned_conference_talks_data.csv'
COLUMN_TO_CLEAN = 'speaker_name_from_html'
SIMILARITY_THRESHOLD_FOR_STANDARDIZATION = 90

def clean_speaker_name_basic(name: str) -> str:
    """
    Performs basic cleaning on a single speaker name.
    - Removes specific problematic characters (e.g., 'Â').
    - Normalizes whitespace (strips leading/trailing, replaces multiple spaces with single).
    """
    if not isinstance(name, str):
        return name # Return as is if not a string (e.g., NaN)

    cleaned_name = name
    # Specific character cleaning (e.g., Â and non-breaking space variants)
    cleaned_name = cleaned_name.replace('Â\xa0', ' ') # Â followed by non-breaking space
    cleaned_name = cleaned_name.replace('Â ', ' ')    # Â followed by regular space
    cleaned_name = cleaned_name.replace('Â', '')       # Standalone Â

    # Normalize general whitespace: replace multiple spaces with a single space, and strip leading/trailing.
    cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()
    
    return cleaned_name

def fix_utf8_encoding_issues(text: str) -> str:
    """
    Fix common UTF-8 double-encoding issues in text.
    
    Handles cases where text was UTF-8, read as Latin-1, then re-encoded as UTF-8.
    Common patterns:
    - Ã¶ → ö (o-umlaut)
    - Ã¤ → ä (a-umlaut)  
    - Ã¼ → ü (u-umlaut)
    - Ã© → é (e-acute)
    - Ã± → ñ (n-tilde)
    - â → " or ' or – (various quotes/dashes)
    """
    if not isinstance(text, str):
        return text
    
    # Dictionary of common UTF-8 encoding fixes
    encoding_fixes = {
        # Umlauts and accented characters
        'Ã¶': 'ö',  # o-umlaut
        'Ã¤': 'ä',  # a-umlaut
        'Ã¼': 'ü',  # u-umlaut
        'Ã–': 'Ö',  # O-umlaut
        'Ã„': 'Ä',  # A-umlaut
        'Ãœ': 'Ü',  # U-umlaut
        'Ã©': 'é',  # e-acute
        'Ã¨': 'è',  # e-grave
        'Ã¡': 'á',  # a-acute
        'Ã ': 'à',  # a-grave
        'Ã­': 'í',  # i-acute
        'Ã³': 'ó',  # o-acute
        'Ãº': 'ú',  # u-acute
        'Ã±': 'ñ',  # n-tilde
        'Ã§': 'ç',  # c-cedilla
        
        # Quote and punctuation marks
        'â': '"',   # Left double quotation mark
        'â': '"',   # Right double quotation mark
        'â': "'",   # Left single quotation mark  
        'â': "'",   # Right single quotation mark
        'â': '–',   # En dash
        'â': '—',   # Em dash
        'â¦': '…',  # Horizontal ellipsis
        'â¢': '•',  # Bullet
        
        # Other common issues
        'Â': '',    # Standalone  (often garbage)
        'Ãâ': 'À',  # A-grave (alternative encoding)
    }
    
    # Apply fixes
    fixed_text = text
    for wrong, correct in encoding_fixes.items():
        fixed_text = fixed_text.replace(wrong, correct)
    
    # Additional cleanup for any remaining  characters followed by spaces
    fixed_text = re.sub(r'Â+\s*', ' ', fixed_text)
    fixed_text = re.sub(r'\s+', ' ', fixed_text).strip()
    
    return fixed_text

def clean_text_comprehensive(text: str) -> str:
    """
    Comprehensive text cleaning that combines encoding fixes and basic cleaning.
    """
    if not isinstance(text, str):
        return text
    
    # First fix UTF-8 encoding issues
    text = fix_utf8_encoding_issues(text)
    
    # Then apply basic cleaning
    text = clean_speaker_name_basic(text)
    
    return text

def build_name_standardization_map(unique_names: list, threshold: int) -> dict:
    """
    Builds a map to standardize similar names. 
    Names with similarity >= threshold will be mapped to a single standard form.
    The standard form is chosen by sorting the pair and picking the first.
    Handles transitive mappings (A->B, B->C => A->C).
    """
    name_map = {name: name for name in unique_names} # Initialize: each name maps to itself
    sorted_unique_names = sorted(list(unique_names)) # Sort for consistent comparison order

    print(f"Building standardization map for {len(sorted_unique_names)} unique names with threshold {threshold}...")
    
    # Prioritize exact or very high similarity matches first if needed, but direct mapping works.
    for name1, name2 in combinations(sorted_unique_names, 2):
        # Ensure we are comparing the current standard forms
        # This helps in making decisions based on already potentially standardized names
        # However, for building the initial map, comparing raw unique names is fine.
        
        # Using token_sort_ratio as it's good for names where word order might differ slightly
        # or for minor typos. For very close matches like initial differences, it should work.
        score = fuzz.token_sort_ratio(name1, name2) 

        if score >= threshold:
            # Determine the standard: alphabetically first of the pair
            standard_name = min(name1, name2)
            variant_name = max(name1, name2)
            
            # Update mapping for the variant, but ensure it points to the ultimate standard
            # If variant_name was already mapped to something, trace it back to its root standard
            # For simplicity here, we map directly. Transitive closure will be handled later.
            current_standard_for_variant = name_map[variant_name]
            if name_map[standard_name] != standard_name: # standard_name itself is a variant
                 # point variant to the standard_name's root
                name_map[variant_name] = name_map[standard_name]
            else:
                name_map[variant_name] = standard_name
            
            # Also ensure the chosen standard_name also maps to itself if it was part of a prior mapping
            # This logic can get complex. A simpler approach is to build direct variant -> standard chosen here
            # And then apply transitive closure.
            
            # Simpler update: map the variant to the chosen standard for this pair
            if name_map[variant_name] != standard_name: # only update if it changes, to avoid loops with transitive step
                 print(f"  Mapping '{variant_name}' (score: {score}) to '{standard_name}'")
                 name_map[variant_name] = standard_name

    # Resolve transitive mappings: ensure all names map to their ultimate root standard
    # Iterate until no more changes are made
    changed_in_pass = True
    passes = 0
    while changed_in_pass and passes < len(unique_names): # Max passes to prevent infinite loops
        changed_in_pass = False
        passes += 1
        for name in sorted_unique_names: # Iterate in defined order
            if name_map[name] != name_map[name_map[name]]: # If name maps to X, and X maps to Y, map name to Y
                if name_map[name] != name: # Don't remap a root to its child if child was re-rooted
                    # print(f"    Resolving transitive: '{name}' from '{name_map[name]}' to '{name_map[name_map[name]]}'")
                    name_map[name] = name_map[name_map[name]]
                    changed_in_pass = True
    print(f"Standardization map built after {passes} passes for transitive closure.")
    return name_map

def main():
    print(f"Starting data cleaning and standardization process...")
    print(f"Reading data from: {INPUT_CSV_PATH}")

    try:
        df = pd.read_csv(INPUT_CSV_PATH)
    except FileNotFoundError:
        print(f"Error: Input file not found at {INPUT_CSV_PATH}")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    if COLUMN_TO_CLEAN not in df.columns:
        print(f"Error: Column '{COLUMN_TO_CLEAN}' not found. Cannot clean.")
        return

    # 1. Apply comprehensive text cleaning to multiple columns
    text_columns_to_clean = [
        COLUMN_TO_CLEAN,  # speaker_name_from_html
        'text_preview',   # Main text content
        'explanation',    # LLM explanation
        'key_phrases',    # Key phrases
        'talk_identifier', # Talk titles
    ]
    
    # Only clean columns that exist in the DataFrame
    existing_text_columns = [col for col in text_columns_to_clean if col in df.columns]
    
    print(f"Applying comprehensive text cleaning (UTF-8 encoding fixes + basic cleaning)...")
    print(f"Cleaning columns: {existing_text_columns}")
    
    for column in existing_text_columns:
        print(f"  Cleaning column: '{column}'...")
        df[column] = df[column].apply(lambda x: clean_text_comprehensive(x) if pd.notna(x) else x)
    
    print(f"Finished comprehensive text cleaning.")

    # 2. Build and apply standardization map for speaker names specifically
    if COLUMN_TO_CLEAN in existing_text_columns:
        unique_names_after_clean = list(df[COLUMN_TO_CLEAN].dropna().unique())
        
        if not unique_names_after_clean:
            print("No unique names found after cleaning to standardize.")
        else:
            name_map = build_name_standardization_map(unique_names_after_clean, SIMILARITY_THRESHOLD_FOR_STANDARDIZATION)
            
            original_names_count = len(unique_names_after_clean)
            standardized_names_count = len(set(name_map.values()))
            
            print(f"Applying standardization map to '{COLUMN_TO_CLEAN}'...")
            df[COLUMN_TO_CLEAN] = df[COLUMN_TO_CLEAN].map(name_map).fillna(df[COLUMN_TO_CLEAN])
            print(f"Finished standardization. Number of unique names reduced from {original_names_count} to {standardized_names_count}.")

    try:
        df.to_csv(OUTPUT_CSV_PATH, index=False)
        print(f"Successfully cleaned and standardized data, saved to: {OUTPUT_CSV_PATH}")
        
        # Print some examples of fixes made
        print(f"\nSample of cleaned data:")
        sample_columns = ['speaker_name_from_html', 'text_preview'] if 'text_preview' in df.columns else ['speaker_name_from_html']
        print(df[sample_columns].head(3).to_string())
        
    except Exception as e:
        print(f"Error writing cleaned data to CSV: {e}")

if __name__ == "__main__":
    main() 