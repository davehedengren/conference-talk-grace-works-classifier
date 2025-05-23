import pandas as pd
from itertools import combinations
from typing import List, Tuple

# Using thefuzz for string matching. Make sure it's installed: pip install thefuzz python-Levenshtein
from thefuzz import fuzz 

DATA_PATH = 'output/labeled_conference_talks_with_speaker_names_20250520.csv'
SPEAKER_COLUMN = 'speaker_name_from_html'
SIMILARITY_THRESHOLD = 75  # Temporarily lowered to catch more variations

def find_similar_names(data_path: str, speaker_column: str, threshold: int) -> List[Tuple[str, str, int]]:
    """
    Finds and returns pairs of similar speaker names from a CSV file.

    Args:
        data_path: Path to the CSV file.
        speaker_column: The name of the column containing speaker names.
        threshold: The minimum similarity score (0-100) to consider names as similar.

    Returns:
        A list of tuples, where each tuple contains two similar names and their similarity score.
    """
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        print(f"Error: The file {data_path} was not found.")
        return []

    if speaker_column not in df.columns:
        print(f"Error: Column '{speaker_column}' not found in the CSV.")
        return []

    # Get unique, non-null speaker names and sort them for consistent pairing
    unique_names = sorted(list(df[speaker_column].dropna().unique()))
    
    if len(unique_names) < 2:
        print("Not enough unique names to compare.")
        return []

    print(f"Found {len(unique_names)} unique speaker names. Comparing pairs...")

    similar_pairs = []
    # Compare all unique pairs of names
    for name1, name2 in combinations(unique_names, 2):
        # Using token_sort_ratio to handle names with words out of order (e.g., "Smith, Joseph" vs "Joseph Smith")
        # and also simple ratio for direct comparison. We can take the higher of the two or be more specific.
        # ratio = fuzz.ratio(str(name1), str(name2)) 
        token_sort_ratio = fuzz.token_sort_ratio(str(name1), str(name2))
        
        # You might want to experiment with different fuzz methods like:
        # - fuzz.ratio(name1, name2) - simple ratio
        # - fuzz.partial_ratio(name1, name2) - good for substrings
        # - fuzz.token_set_ratio(name1, name2) - ignores word order and duplicated words

        if token_sort_ratio >= threshold:
            similar_pairs.append((name1, name2, token_sort_ratio))
            
    # Sort by score descending, then by name
    similar_pairs.sort(key=lambda x: (x[2], x[0], x[1]), reverse=True)

    return similar_pairs

if __name__ == "__main__":
    print(f"Looking for similar names in '{DATA_PATH}', column '{SPEAKER_COLUMN}' with threshold >={SIMILARITY_THRESHOLD}...")
    
    similar_found = find_similar_names(DATA_PATH, SPEAKER_COLUMN, SIMILARITY_THRESHOLD)

    if similar_found:
        print(f"\nFound {len(similar_found)} pairs of potentially similar names:")
        for name1, name2, score in similar_found:
            print(f"- '{name1}' AND '{name2}' (Score: {score})")
        print("\nConsider standardizing these names in your dataset or during analysis.")
    else:
        print("No significantly similar names found with the current threshold.") 