import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# Load the data
DATA_PATH = 'output/cleaned_conference_talks_data.csv'

@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    
    # Filter out rows where speaker name contains "Presented by"
    # Ensure the column exists and handle potential NaN values by converting to string first
    if 'speaker_name_from_html' in df.columns:
        df = df[~df['speaker_name_from_html'].astype(str).str.contains("Presented by", case=False, na=False)]
    else:
        st.warning("Column 'speaker_name_from_html' not found. Cannot filter out 'Presented by' entries.")

    # Convert year and month to a datetime object for proper sorting and plotting
    # Assuming 'month' is a string like 'April' or 'October' or a number 1-12
    # For simplicity, mapping 'April' to month 4 and 'October' to month 10
    # If month is already numeric, this step might need adjustment or can be simpler
    if df['month'].dtype == 'object':
        # Ensure all expected month strings are mapped
        month_map = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4, 
            'May': 5, 'June': 6, 'July': 7, 'August': 8, 
            'September': 9, 'October': 10, 'November': 11, 'December': 12
        }
        # Handle cases where month might not be in map (e.g. if it's already numeric as a string)
        df['month_numeric'] = df['month'].apply(
            lambda x: month_map.get(x, pd.to_numeric(x, errors='coerce')) if isinstance(x, str) else x
        )
        # Coerce to int after potential mixed types, then to string for concatenation
        df['month_numeric'] = pd.to_numeric(df['month_numeric'], errors='coerce').fillna(0).astype(int)
        df['conference_date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month_numeric'].astype(str) + '-01', errors='coerce')
    else: # Assuming month is already numeric
        df['conference_date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'].astype(str) + '-01', errors='coerce')
    
    df = df.sort_values('conference_date')
    return df

st.set_page_config(layout="wide")
st.title("Conference Talk Grace-Works Classifier Analysis")

df = load_data(DATA_PATH)

if df is not None and not df.empty:
    st.header("Raw Data Preview")
    st.dataframe(df.head())

    # --- Time Series Analysis ---
    st.header("Grace-Works Score Over Time")
    
    # Ensure 'conference_date' and 'score' are present
    if 'conference_date' in df.columns and 'score' in df.columns:
        # Group by conference session (year and month)
        # For display, we'll create a 'Session' column
        df['session_str'] = df['year'].astype(str) + '-' + df['month'].astype(str)

        # Using conference_date for proper time-series plotting
        # Reverting to a more compatible aggregation syntax for pandas 1.3.5
        time_series_data = df.groupby('conference_date')['score'].agg(
            ['mean', lambda x: x.quantile(0.25), lambda x: x.quantile(0.75)]
        ).reset_index()
        time_series_data.columns = ['conference_date', 'mean_score', 'p25_score', 'p75_score'] # Explicitly name columns
        
        # Melt the DataFrame for Altair
        time_series_melted = time_series_data.melt(
            id_vars=['conference_date'], 
            value_vars=['mean_score', 'p25_score', 'p75_score'],
            var_name='Metric', 
            value_name='Score'
        )
        
        # Rename metrics for a nicer legend
        metric_rename_map = {
            'mean_score': 'Mean Score',
            'p25_score': 'P25 Score',
            'p75_score': 'P75 Score'
        }
        time_series_melted['Metric'] = time_series_melted['Metric'].map(metric_rename_map)

        chart = alt.Chart(time_series_melted).mark_line().encode(
            x=alt.X('conference_date:T', title='Conference Date'),
            y=alt.Y('Score:Q', scale=alt.Scale(domain=[-3, 3]), title='Grace-Works Score'),
            color='Metric:N',
            tooltip=['conference_date:T', 'Metric:N', 'Score:Q']
        ).properties(
            title='Grace-Works Score Over Time'
        ).interactive()

        st.altair_chart(chart, use_container_width=True)
        st.caption("This chart shows the mean, 25th percentile (P25), and 75th percentile (P75) of the 'score' for each conference session over time. A higher score indicates a 'works' focus, while a lower score indicates a 'grace' focus. Y-axis is fixed from -3 to +3.")

    else:
        st.warning("Required columns ('conference_date' and/or 'score') not found for time series analysis.")


    # --- Speaker Analysis ---
    st.header("Speaker Analysis")
    if 'speaker_name_from_html' in df.columns and 'score' in df.columns:
        speaker_scores = df.groupby('speaker_name_from_html')['score'].agg(['mean', 'count']).reset_index()
        speaker_scores.columns = ['Speaker Name', 'Average Score', 'Number of Talks']
        
        # Filter for speakers with at least 5 talks
        speaker_scores_filtered = speaker_scores[speaker_scores['Number of Talks'] >= 5]

        st.subheader("Most Works-Focused Speakers (Highest Average Score, >= 5 Talks)")
        st.dataframe(speaker_scores_filtered.sort_values('Average Score', ascending=False).head(10))

        st.subheader("Most Grace-Focused Speakers (Lowest Average Score, >= 5 Talks)")
        st.dataframe(speaker_scores_filtered.sort_values('Average Score', ascending=True).head(10))
        
        st.caption("Speakers with a higher average score tend to focus more on 'works', while those with a lower average score focus more on 'grace'. Lists are filtered for speakers with at least 5 talks.")

    else:
        st.warning("Required columns ('speaker_name_from_html' and/or 'score') not found for speaker analysis.")

    # --- Score Distribution ---
    st.header("Overall Score Distribution")
    if 'score' in df.columns:
        st.bar_chart(df['score'].value_counts().sort_index())
        st.caption("This histogram shows the distribution of scores across all talks. Scores range from -3 (heavy grace focus) to +3 (heavy works focus).")
    else:
        st.warning("Required column 'score' not found for score distribution analysis.")
        
    # --- Further Analysis Ideas ---
    st.header("Further Analysis Ideas")
    st.markdown("""
    - **Score by Conference Name/Type:** If there are different types of conferences (e.g., General Conference, BYU Devotional), analyze scores separately.
    - **Trend Lines:** Add trend lines to the time series plot.
    - **Word Clouds:** Generate word clouds for talks classified at extremes (e.g., scores -3 and +3) to see common themes.
    - **Interactive Filtering:** Allow users to filter data by year, speaker, or score range.
    """)

else:
    st.error(f"Could not load or process data from {DATA_PATH}. Please ensure the file exists and is a valid CSV.")

st.sidebar.header("About")
st.sidebar.info(
    "This app visualizes the analysis of conference talks, classifying them on a scale of "
    "grace (-3) to works (+3). Use the charts to explore trends over time and by speaker."
)
st.sidebar.info(f"Data source: `{DATA_PATH}`") 