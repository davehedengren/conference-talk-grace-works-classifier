#!/usr/bin/env python3
"""
Type-hinted Streamlit app for Conference Talk Grace-Works Classifier Analysis.

This module provides a comprehensive dashboard for analyzing conference talk classifications
with proper type safety and modular function design.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

# Configuration
DATA_PATH: str = "output/cleaned_conference_talks_data.csv"
REQUIRED_COLUMNS: List[str] = ["year", "month", "score", "speaker_name_from_html"]
MONTH_MAP: Dict[str, int] = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


@st.cache_data
def load_data(path: str) -> Optional[pd.DataFrame]:
    """
    Load and preprocess conference talk data from CSV file.

    Args:
        path: Path to the CSV file

    Returns:
        Processed DataFrame or None if loading fails
    """
    try:
        df = pd.read_csv(path)

        # Filter out rows where speaker name contains "Presented by"
        if "speaker_name_from_html" in df.columns:
            df = df[
                ~df["speaker_name_from_html"]
                .astype(str)
                .str.contains("Presented by", case=False, na=False)
            ]
        else:
            st.warning(
                "Column 'speaker_name_from_html' not found. Cannot filter out 'Presented by' entries."
            )

        # Process datetime information
        df = _process_datetime_columns(df)

        # Sort by conference date
        if "conference_date" in df.columns:
            df = df.sort_values("conference_date")

        return df

    except Exception as e:
        st.error(f"Error loading data from {path}: {e}")
        return None


def _process_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process year and month columns to create proper datetime objects.

    Args:
        df: Input DataFrame

    Returns:
        DataFrame with processed datetime columns
    """
    if "year" not in df.columns or "month" not in df.columns:
        return df

    # Handle month conversion
    if df["month"].dtype == "object":
        df["month_numeric"] = df["month"].apply(_convert_month_to_numeric)
    else:
        df["month_numeric"] = pd.to_numeric(df["month"], errors="coerce")

    # Create conference_date column
    df["month_numeric"] = df["month_numeric"].fillna(0).astype(int)
    df["conference_date"] = pd.to_datetime(
        df["year"].astype(str) + "-" + df["month_numeric"].astype(str) + "-01", errors="coerce"
    )

    return df


def _convert_month_to_numeric(month_value: Any) -> float:
    """
    Convert month string or number to numeric value.

    Args:
        month_value: Month as string or number

    Returns:
        Numeric month value or NaN if conversion fails
    """
    if isinstance(month_value, str):
        return float(MONTH_MAP.get(month_value, pd.to_numeric(month_value, errors="coerce")))
    return float(month_value) if pd.notna(month_value) else np.nan


def create_time_series_data(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Create time series aggregated data for plotting.

    Args:
        df: Input DataFrame with conference data

    Returns:
        Aggregated time series DataFrame or None if required columns missing
    """
    if not all(col in df.columns for col in ["conference_date", "score"]):
        return None

    # Group by conference date and calculate statistics
    time_series_data = (
        df.groupby("conference_date")["score"]
        .agg(["mean", lambda x: x.quantile(0.25), lambda x: x.quantile(0.75)])
        .reset_index()
    )

    time_series_data.columns = ["conference_date", "mean_score", "p25_score", "p75_score"]

    return time_series_data


def create_time_series_chart(time_series_data: pd.DataFrame) -> Any:
    """
    Create Altair time series chart for grace-works scores.

    Args:
        time_series_data: Aggregated time series data

    Returns:
        Altair chart object
    """
    # Melt the DataFrame for Altair
    time_series_melted = time_series_data.melt(
        id_vars=["conference_date"],
        value_vars=["mean_score", "p25_score", "p75_score"],
        var_name="Metric",
        value_name="Score",
    )

    # Rename metrics for better legend
    metric_rename_map = {
        "mean_score": "Mean Score",
        "p25_score": "P25 Score",
        "p75_score": "P75 Score",
    }
    time_series_melted["Metric"] = time_series_melted["Metric"].map(metric_rename_map)

    chart = (
        alt.Chart(time_series_melted)
        .mark_line()
        .encode(
            x=alt.X("conference_date:T", title="Conference Date"),
            y=alt.Y("Score:Q", scale=alt.Scale(domain=[-3, 3]), title="Grace-Works Score"),
            color="Metric:N",
            tooltip=["conference_date:T", "Metric:N", "Score:Q"],
        )
        .properties(title="Grace-Works Score Over Time")
        .interactive()
    )

    return chart


def create_speaker_analysis_data(df: pd.DataFrame, min_talks: int = 5) -> Optional[pd.DataFrame]:
    """
    Create speaker analysis data with average scores and talk counts.

    Args:
        df: Input DataFrame
        min_talks: Minimum number of talks required for inclusion

    Returns:
        Speaker analysis DataFrame or None if required columns missing
    """
    if not all(col in df.columns for col in ["speaker_name_from_html", "score"]):
        return None

    speaker_scores = (
        df.groupby("speaker_name_from_html")["score"].agg(["mean", "count"]).reset_index()
    )
    speaker_scores.columns = ["Speaker Name", "Average Score", "Number of Talks"]

    # Filter for speakers with minimum talks
    speaker_scores_filtered = speaker_scores[speaker_scores["Number of Talks"] >= min_talks]

    return speaker_scores_filtered


def display_time_series_analysis(df: pd.DataFrame) -> None:
    """
    Display time series analysis section.

    Args:
        df: Conference talk DataFrame
    """
    st.header("Grace-Works Score Over Time")

    time_series_data = create_time_series_data(df)
    if time_series_data is not None:
        chart = create_time_series_chart(time_series_data)
        st.altair_chart(chart, use_container_width=True)
        st.caption(
            "This chart shows the mean, 25th percentile (P25), and 75th percentile (P75) "
            "of the 'score' for each conference session over time. A higher score indicates "
            "a 'works' focus, while a lower score indicates a 'grace' focus. "
            "Y-axis is fixed from -3 to +3."
        )
    else:
        st.warning(
            "Required columns ('conference_date' and/or 'score') not found for time series analysis."
        )


def display_speaker_analysis(df: pd.DataFrame, min_talks: int = 5) -> None:
    """
    Display speaker analysis section.

    Args:
        df: Conference talk DataFrame
        min_talks: Minimum number of talks for speaker inclusion
    """
    st.header("Speaker Analysis")

    speaker_data = create_speaker_analysis_data(df, min_talks)
    if speaker_data is not None:
        st.subheader(f"Most Works-Focused Speakers (Highest Average Score, >= {min_talks} Talks)")
        st.dataframe(speaker_data.sort_values("Average Score", ascending=False).head(10))

        st.subheader(f"Most Grace-Focused Speakers (Lowest Average Score, >= {min_talks} Talks)")
        st.dataframe(speaker_data.sort_values("Average Score", ascending=True).head(10))

        st.caption(
            f"Speakers with a higher average score tend to focus more on 'works', "
            f"while those with a lower average score focus more on 'grace'. "
            f"Lists are filtered for speakers with at least {min_talks} talks."
        )
    else:
        st.warning(
            "Required columns ('speaker_name_from_html' and/or 'score') not found for speaker analysis."
        )


def display_score_distribution(df: pd.DataFrame) -> None:
    """
    Display score distribution analysis.

    Args:
        df: Conference talk DataFrame
    """
    st.header("Overall Score Distribution")

    if "score" in df.columns:
        score_counts = df["score"].value_counts().sort_index()
        st.bar_chart(score_counts)
        st.caption(
            "This histogram shows the distribution of scores across all talks. "
            "Scores range from -3 (heavy grace focus) to +3 (heavy works focus)."
        )
    else:
        st.warning("Required column 'score' not found for score distribution analysis.")


def display_further_analysis_ideas() -> None:
    """Display suggestions for further analysis."""
    st.header("Further Analysis Ideas")
    st.markdown(
        """
    - **Score by Conference Name/Type:** If there are different types of conferences 
      (e.g., General Conference, BYU Devotional), analyze scores separately.
    - **Trend Lines:** Add trend lines to the time series plot.
    - **Word Clouds:** Generate word clouds for talks classified at extremes 
      (e.g., scores -3 and +3) to see common themes.
    - **Interactive Filtering:** Allow users to filter data by year, speaker, or score range.
    - **Statistical Tests:** Perform statistical tests to identify significant trends over time.
    - **Correlation Analysis:** Analyze correlations between speakers, time periods, and scores.
    """
    )


def display_sidebar_info(data_path: str) -> None:
    """
    Display sidebar information.

    Args:
        data_path: Path to the data file
    """
    st.sidebar.header("About")
    st.sidebar.info(
        "This app visualizes the analysis of conference talks, classifying them on a scale of "
        "grace (-3) to works (+3). Use the charts to explore trends over time and by speaker."
    )
    st.sidebar.info(f"Data source: `{data_path}`")


def validate_data_requirements(df: Optional[pd.DataFrame]) -> bool:
    """
    Validate that the DataFrame meets basic requirements.

    Args:
        df: DataFrame to validate

    Returns:
        True if data is valid, False otherwise
    """
    if df is None or df.empty:
        return False

    # Check for essential columns
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        st.warning(f"Missing required columns: {missing_columns}")
        return False

    return True


def main() -> None:
    """Main application function."""
    # Page configuration
    st.set_page_config(
        layout="wide", page_title="Conference Talk Grace-Works Analysis", page_icon="📖"
    )

    st.title("Conference Talk Grace-Works Classifier Analysis")

    # Load and validate data
    df = load_data(DATA_PATH)

    if not validate_data_requirements(df):
        st.error(
            f"Could not load or process data from {DATA_PATH}. Please ensure the file exists and is a valid CSV."
        )
        return

    # Type assertion since we've validated the data
    assert df is not None

    # Display data preview
    st.header("Raw Data Preview")
    st.dataframe(df.head())

    # Main analysis sections
    display_time_series_analysis(df)
    display_speaker_analysis(df, min_talks=5)
    display_score_distribution(df)
    display_further_analysis_ideas()

    # Sidebar
    display_sidebar_info(DATA_PATH)


if __name__ == "__main__":
    main()
