import streamlit as st
import pandas as pd
import altair as alt # Using altair for consistency if charts are added later

# --- Data Loading (copied from main streamlit_app.py for this page) ---
DATA_PATH = 'output/cleaned_conference_talks_data.csv' # Ensure this is your latest cleaned file
# CONFERENCE_ID_COLUMN = 'talk_identifier' # No longer used for main filter
SPEAKER_NAME_COLUMN = 'speaker_name_from_html'
SCORE_COLUMN = 'score'
# MIN_TALKS_DEFAULT = 5 # No longer using this default for this specific page

@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    
    if SPEAKER_NAME_COLUMN in df.columns:
        df = df[~df[SPEAKER_NAME_COLUMN].astype(str).str.contains("Presented by", case=False, na=False)]

    # Ensure year and month columns are suitable for filtering
    if 'year' in df.columns:
        df['year'] = pd.to_numeric(df['year'], errors='coerce').dropna().astype(int)
    if 'month' in df.columns: # Keep month as is for now, will use numeric mapping or direct numeric value
        pass 
        
    # Create conference_date for robust date operations if year and month exist
    if 'year' in df.columns and 'month' in df.columns:
        # Attempt to create month_numeric more robustly
        if df['month'].dtype == 'object':
            month_map = {
                'January': 1, 'February': 2, 'March': 3, 'April': 4, 
                'May': 5, 'June': 6, 'July': 7, 'August': 8, 
                'September': 9, 'October': 10, 'November': 11, 'December': 12
            }
            # Handle if month is already a number but stored as string, or a name
            df['month_numeric'] = df['month'].apply(
                lambda x: month_map.get(str(x).title(), pd.to_numeric(x, errors='coerce')) if pd.notna(x) else None
            )
        else: # if month column is already numeric
            df['month_numeric'] = pd.to_numeric(df['month'], errors='coerce')
        
        df['month_numeric'] = df['month_numeric'].dropna().astype(int)
        df = df[df['month_numeric'].between(1, 12)] # Ensure valid months

        df['conference_date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month_numeric'].astype(str) + '-01', errors='coerce')
        df = df.dropna(subset=['conference_date']) # Drop rows where date conversion failed
        df = df.sort_values('conference_date')
    return df

# --- Streamlit Page Setup ---
st.set_page_config(layout="wide", page_title="Speaker Explorer")
st.title("🏆 Speaker Explorer by Date Range")

st.markdown("""
Analyze speaker scores (grace vs. works) filtered by a selected year range and specific months.
""")

df_full = load_data(DATA_PATH)

if df_full is not None and not df_full.empty and 'year' in df_full.columns and 'month_numeric' in df_full.columns and SPEAKER_NAME_COLUMN in df_full.columns and SCORE_COLUMN in df_full.columns:
    
    st.sidebar.header("Filters")
    
    # --- Year Range Filter ---
    min_year, max_year = int(df_full['year'].min()), int(df_full['year'].max())
    selected_year_range = st.sidebar.slider(
        "Select Year Range",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year) # Default to full range
    )
    
    # --- Simplified Month Filter for April & October ---
    month_choice_options = ["April & October", "April Only", "October Only"]
    month_selection = st.sidebar.radio(
        "Select Conference Month(s)",
        options=month_choice_options,
        index=0 # Default to "April & October"
    )

    selected_month_numbers = []
    if month_selection == "April & October":
        selected_month_numbers = [4, 10]
        selected_month_names_display = "April, October"
    elif month_selection == "April Only":
        selected_month_numbers = [4]
        selected_month_names_display = "April"
    elif month_selection == "October Only":
        selected_month_numbers = [10]
        selected_month_names_display = "October"

    # Filter DataFrame based on selections
    df_filtered = df_full[
        (df_full['year'] >= selected_year_range[0]) &
        (df_full['year'] <= selected_year_range[1]) &
        (df_full['month_numeric'].isin(selected_month_numbers))
    ].copy()

    if df_filtered.empty:
        st.warning("No data available for the selected date range and month(s). Please adjust filters.")
    else:
        st.header("Speaker Analysis Results")
        st.markdown(f"Showing results for years: **{selected_year_range[0]} - {selected_year_range[1]}**")
        st.markdown(f"For month(s): **{selected_month_names_display}**")
        # st.caption(f"Speakers must have at least **{min_talks_slider}** talk(s) in the selected period to be listed.") # Caption removed

        speaker_scores = df_filtered.groupby(SPEAKER_NAME_COLUMN)[SCORE_COLUMN].agg(['mean', 'count']).reset_index()
        speaker_scores.columns = ['Speaker Name', 'Average Score', 'Number of Talks']
        
        speaker_scores_to_display = speaker_scores # Use all speaker_scores

        if speaker_scores_to_display.empty:
            st.info(f"No speakers found for the current filter.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader(f"Most Works-Focused (Avg Score)")
                st.dataframe(speaker_scores_to_display.sort_values('Average Score', ascending=False).head(10), height=400)
            
            with col2:
                st.subheader(f"Most Grace-Focused (Avg Score)")
                st.dataframe(speaker_scores_to_display.sort_values('Average Score', ascending=True).head(10), height=400)
else:
    if df_full is None or df_full.empty:
        st.error(f"Could not load or process data from {DATA_PATH}.")
    elif not all(col in df_full.columns for col in ['year', 'month_numeric', SPEAKER_NAME_COLUMN, SCORE_COLUMN]):
        missing_cols = [col for col in ['year', 'month_numeric', SPEAKER_NAME_COLUMN, SCORE_COLUMN] if col not in df_full.columns]
        st.warning(f"The loaded CSV is missing required columns for this page: { ', '.join(missing_cols)}. Ensure 'year' and 'month' (or 'month_numeric') are present and correctly processed.")

st.sidebar.info(f"Data source: `{DATA_PATH}`") 