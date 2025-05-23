import streamlit as st
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# --- Data Loading (copied from main streamlit_app.py for this page) ---
DATA_PATH = 'output/cleaned_conference_talks_data.csv' # Ensure this is your latest cleaned file

@st.cache_data
def load_data(path):
    df = pd.read_csv(path)

    # Filter out rows where speaker name contains "Presented by"
    # Ensure the column exists and handle potential NaN values by converting to string first
    if 'speaker_name_from_html' in df.columns:
        df = df[~df['speaker_name_from_html'].astype(str).str.contains("Presented by", case=False, na=False)]
    # No need for an st.warning here as it's a sub-page, assuming main app would catch column absence.

    # Convert year and month to a datetime object for proper sorting and plotting
    if df['month'].dtype == 'object':
        month_map = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4, 
            'May': 5, 'June': 6, 'July': 7, 'August': 8, 
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }
        df['month_numeric'] = df['month'].apply(
            lambda x: month_map.get(x, pd.to_numeric(x, errors='coerce')) if isinstance(x, str) else x
        )
        df['month_numeric'] = pd.to_numeric(df['month_numeric'], errors='coerce').fillna(0).astype(int)
        df['conference_date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month_numeric'].astype(str) + '-01', errors='coerce')
    else: # Assuming month is already numeric
        df['conference_date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'].astype(str) + '-01', errors='coerce')
    
    df = df.sort_values('conference_date')
    return df

# --- Word Cloud Generation Function ---
def generate_wordcloud_from_key_phrases(phrases_series, title):
    """Generates and displays a word cloud from a series of comma-separated key phrases."""
    # Concatenate all non-null key phrase strings, then join them
    # Split by comma, strip whitespace from each phrase, filter out empty phrases
    all_phrases = []
    for item in phrases_series.dropna():
        all_phrases.extend([phrase.strip() for phrase in item.split(',') if phrase.strip()])
    
    text_for_wordcloud = " ".join(all_phrases)

    if not text_for_wordcloud:
        st.write(f"No key phrases available to generate word cloud for {title.lower()}.")
        return

    try:
        wordcloud = WordCloud(width=800, height=400, background_color='white', collocations=False).generate(text_for_wordcloud)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig)
    except Exception as e:
        st.error(f"Could not generate word cloud for {title.lower()}: {e}")
        st.write("Raw text for word cloud generation (first 500 chars):")
        st.text(text_for_wordcloud[:500])


# --- Streamlit Page Setup ---
st.set_page_config(layout="wide", page_title="Key Phrase Word Clouds")
st.title("Key Phrase Word Clouds for Extreme Scores")

st.markdown("""
This page displays word clouds generated from the `key_phrases` associated with talks
that received the most extreme scores: +3 (most works-focused) and -3 (most grace-focused).
The `key_phrases` are extracted by the LLM during the classification process.
""")

df_full = load_data(DATA_PATH)

if df_full is not None and not df_full.empty and 'score' in df_full.columns and 'key_phrases' in df_full.columns:
    # Filter for score > 2.5 (more works-focused)
    df_works_focused = df_full[df_full['score'] > 2.5]
    st.header("Word Cloud for Scores > +2.5 (Highly Works-Focused)")
    if not df_works_focused.empty:
        generate_wordcloud_from_key_phrases(df_works_focused['key_phrases'], "Highly Works-Focused Talks (Score > 2.5)")
        st.caption(f"Generated from {len(df_works_focused)} talks.")
    else:
        st.write("No talks found with a score greater than +2.5.")

    # Filter for score < -2.5 (more grace-focused)
    df_grace_focused = df_full[df_full['score'] < -2.5]
    st.header("Word Cloud for Scores < -2.5 (Highly Grace-Focused)")
    if not df_grace_focused.empty:
        generate_wordcloud_from_key_phrases(df_grace_focused['key_phrases'], "Highly Grace-Focused Talks (Score < -2.5)")
        st.caption(f"Generated from {len(df_grace_focused)} talks.")
    else:
        st.write("No talks found with a score less than -2.5.")
        
    st.markdown("""
    ---
    **Note on Word Cloud Generation:**
    - The word clouds are generated by concatenating all key phrases for the selected talks.
    - Phrases are split by commas.
    - Common words might appear larger if they are frequent within the extracted key phrases.
    - `collocations=False` is used to prevent common bigrams from dominating too much, focusing more on individual words/phrases.
    """)

else:
    if df_full is None or df_full.empty:
        st.error(f"Could not load or process data from {DATA_PATH}. Please ensure the file exists and is a valid CSV.")
    else:
        st.warning("The loaded CSV must contain 'score' and 'key_phrases' columns to generate word clouds.") 