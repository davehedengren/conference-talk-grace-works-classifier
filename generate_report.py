import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import os
from datetime import datetime

def generate_report(csv_filepath):
    """
    Loads data from a CSV file, generates various plots, saves them,
    and creates a markdown report with embedded charts and trend explanations.
    """
    try:
        df = pd.read_csv(csv_filepath)
    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_filepath}")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    if df.empty:
        print("CSV file is empty. No report will be generated.")
        return

    # --- Directory Setup ---
    report_dir = os.path.join("output", "reports")
    os.makedirs(report_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_md_filename = os.path.join(report_dir, f"report_{timestamp}.md")
    
    # --- Data Cleaning/Preparation ---
    # Ensure 'year' is integer for plotting (extract from conference_session_id or year column)
    if 'year' in df.columns:
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
    elif 'conference_session_id' in df.columns:
        df['year'] = df['conference_session_id'].astype(str).str.split('-').str[0]
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
    else:
        print("Warning: Could not determine 'year' for plotting score by year.")

    df.dropna(subset=['year', 'score'], inplace=True) # Drop rows where essential data is missing

    # --- Chart Generation ---
    charts = {} # To store filenames of generated charts

    # 1. Score by Year (Line Plot)
    if 'year' in df.columns and 'score' in df.columns and not df.empty:
        plt.figure(figsize=(10, 6))
        # Convert year to int for correct sorting and display on axis
        df_agg_year = df.groupby(df['year'].astype(int))['score'].mean().reset_index()

        sns.lineplot(data=df_agg_year, x='year', y='score', marker='o')
        plt.title('Average Score by Year')
        plt.xlabel('Year')
        plt.ylabel('Average Score')
        plt.grid(True)
        chart_filename = os.path.join(report_dir, f"score_by_year_{timestamp}.png")
        plt.savefig(chart_filename)
        plt.close()
        charts['score_by_year'] = os.path.relpath(chart_filename) # Relative path for markdown
        print(f"Generated: {chart_filename}")
    else:
        print("Skipping 'Score by Year' plot due to missing 'year' or 'score' data or empty dataframe after cleaning.")


    # 2. Score Distribution (Histogram/KDE)
    if 'score' in df.columns and not df.empty:
        plt.figure(figsize=(10, 6))
        sns.histplot(df['score'], kde=True, bins=range(int(df['score'].min()), int(df['score'].max()) + 2) , discrete=False) # Bins for -3 to +3
        plt.title('Distribution of Scores')
        plt.xlabel('Score')
        plt.ylabel('Frequency')
        chart_filename = os.path.join(report_dir, f"score_distribution_{timestamp}.png")
        plt.savefig(chart_filename)
        plt.close()
        charts['score_distribution'] = os.path.relpath(chart_filename)
        print(f"Generated: {chart_filename}")
    else:
        print("Skipping 'Score Distribution' plot due to missing 'score' data or empty dataframe.")

    # 3. Average Score per Speaker (Bar Chart - Top N)
    if 'speaker_name' in df.columns and 'score' in df.columns and not df.empty:
        # Filter out "Unknown Speaker" before calculating averages and top N
        df_known_speakers = df[df['speaker_name'].str.lower() != 'unknown speaker']
        if not df_known_speakers.empty:
            speaker_scores = df_known_speakers.groupby('speaker_name')['score'].agg(['mean', 'count']).reset_index()
            speaker_scores = speaker_scores.sort_values(by='mean', ascending=False)
            
            top_n = min(20, len(speaker_scores)) # Show top 20 or fewer if not enough speakers
            
            if top_n > 0:
                plt.figure(figsize=(12, 8))
                sns.barplot(data=speaker_scores.head(top_n), x='mean', y='speaker_name', palette="viridis")
                plt.title(f'Top {top_n} Speakers by Average Score (Count of talks indicated by bar length)')
                plt.xlabel('Average Score')
                plt.ylabel('Speaker Name')
                plt.tight_layout() # Adjust layout to prevent labels from being cut off
                chart_filename = os.path.join(report_dir, f"avg_score_per_speaker_{timestamp}.png")
                plt.savefig(chart_filename)
                plt.close()
                charts['avg_score_per_speaker'] = os.path.relpath(chart_filename)
                print(f"Generated: {chart_filename}")
            else:
                 print("Skipping 'Average Score per Speaker' plot as no known speakers found after filtering.")
        else:
            print("Skipping 'Average Score per Speaker' plot as no data with known speakers available.")
    else:
        print("Skipping 'Average Score per Speaker' plot due to missing 'speaker_name' or 'score' data or empty dataframe.")

    # --- Markdown Report Generation ---
    with open(report_md_filename, 'w') as f:
        f.write(f"# Conference Talk Analysis Report\n\n")
        f.write(f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source CSV: `{os.path.basename(csv_filepath)}`\n\n")
        f.write("## Overview\n")
        f.write(f"This report analyzes {len(df)} talks processed from the input CSV file.\n\n")

        if 'score_by_year' in charts:
            f.write("### Average Score Over Time\n")
            f.write(f"![Average Score by Year]({charts['score_by_year']})\n")
            f.write("**Trend:** (Interpret and describe the trend observed in the score by year chart. e.g., 'The average score shows a slight upward trend from 2020 to 2023, followed by a dip in 2024.' or 'Scores have remained relatively consistent across the observed years.')\n\n")
        
        if 'score_distribution' in charts:
            f.write("### Distribution of Scores\n")
            f.write(f"![Score Distribution]({charts['score_distribution']})\n")
            f.write("**Observation:** (Interpret and describe the distribution. e.g., 'The scores are predominantly clustered around 0 and +1, suggesting a general tendency towards a neutral to slightly positive theological emphasis in the analyzed talks. There are fewer talks with extreme scores (-3 or +3).' or 'The distribution is bimodal, with peaks at -2 and +2.')\n\n")

        if 'avg_score_per_speaker' in charts:
            f.write("### Average Score by Speaker\n")
            f.write(f"![Average Score by Speaker]({charts['avg_score_per_speaker']})\n")
            f.write("**Observation:** (Interpret and describe. e.g., 'Speaker X and Speaker Y consistently have higher average scores, indicating their talks often lean more towards one end of the spectrum. The number of talks per speaker varies, which should be considered when interpreting these averages.')\n\n")
        
        f.write("## Further Analysis Suggestions\n")
        f.write("- Explore correlations between key phrases and scores.\n")
        f.write("- Analyze trends within specific conference sessions or for prolific speakers.\n")
        f.write("- Consider sentiment analysis of the 'explanation' field for deeper qualitative insights.\n")

    print(f"\nMarkdown report generated: {report_md_filename}")

def main():
    parser = argparse.ArgumentParser(description="Generate a report with charts from a conference talk scores CSV file.")
    parser.add_argument("csv_filepath", type=str, help="Path to the input CSV file (e.g., output/conference_talk_scores_YYYYMMDD_HHMMSS.csv)")
    args = parser.parse_args()

    generate_report(args.csv_filepath)

if __name__ == "__main__":
    main() 