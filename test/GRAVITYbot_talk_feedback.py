"""
talk_feedback.py

Purpose:
    Extracts human responses to GRAVITYbot summary posts from Talk forum data.
    Filters out the bot's own posts to capture citizen scientist feedback/discussion.
    
    Used for research analysis of how users engage with automated summaries.

Output:
    - Appends new feedback to DATA_FOLDER/GRAVITYbot_talk_discussion.csv
    - Writes deduplicated version to OUTPUT_FOLDER/GRAVITYbot_talk_discussion.csv
"""

import datetime
import os
import sys

import pandas

# Add project root to path for config import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config


# GRAVITYbot-related board IDs (where summaries get posted)
GRAVITYBOT_BOARDS = [6872, 6945, 6946]

# User IDs to exclude (bots and system accounts)
EXCLUDED_USER_IDS = [
    2630456,   # Unknown - possibly another bot or test account
    2877652,   # GRAVITYbot
]


def extract_feedback(date_str=None):
    """
    Extracts human feedback from GRAVITYbot discussion boards.
    
    Args:
        date_str (str, optional): Date string (YYYY-MM-DD) for the Talk export.
            Defaults to today's date.
    
    Returns:
        pandas.DataFrame: Filtered feedback data, or None if source file not found.
    """
    if date_str is None:
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
    
    json_path = config.DATA_FOLDER_PATH / f"project-1104-comments_{date_str}.json"
    csv_path = config.DATA_FOLDER_PATH / f"project-1104-comments_{date_str}.csv"
    
    # Convert JSON to CSV if needed
    if not csv_path.exists():
        if not json_path.exists():
            print(f"Source file not found: {json_path}")
            return None
        
        print(f"Converting {json_path} to CSV...")
        talk_json = pandas.read_json(json_path)
        talk_json.to_csv(csv_path, index=False)
    
    # Load and filter data
    print(f"Loading {csv_path}...")
    talk_data = pandas.read_csv(csv_path)
    
    # Keep only GRAVITYbot-related boards
    talk_data = talk_data[talk_data.board_id.isin(GRAVITYBOT_BOARDS)]
    print(f"Filtered to {len(talk_data)} posts on GRAVITYbot boards")
    
    # Remove bot posts
    talk_data = talk_data[~talk_data.comment_user_id.isin(EXCLUDED_USER_IDS)]
    print(f"After removing bot posts: {len(talk_data)} human responses")
    
    return talk_data


def save_feedback(feedback_data):
    """
    Appends feedback data to cumulative file and writes deduplicated version.
    
    Args:
        feedback_data (pandas.DataFrame): Filtered feedback to save.
    """
    cumulative_path = config.DATA_FOLDER_PATH / "GRAVITYbot_talk_discussion.csv"
    deduplicated_path = config.OUTPUT_FOLDER_PATH / "GRAVITYbot_talk_discussion.csv"
    
    # Append to cumulative file
    write_header = not cumulative_path.exists()
    feedback_data.to_csv(cumulative_path, mode='a', header=write_header, index=False)
    print(f"Appended {len(feedback_data)} rows to {cumulative_path}")
    
    # Write deduplicated version
    all_data = pandas.read_csv(cumulative_path).drop_duplicates()
    all_data.to_csv(deduplicated_path, index=False)
    print(f"Wrote {len(all_data)} unique rows to {deduplicated_path}")


def main(date_str=None):
    """
    Main entry point for feedback extraction.
    
    Args:
        date_str (str, optional): Date to process. Defaults to today.
    """
    print(f"Data folder: {config.DATA_FOLDER_PATH}")
    print(f"Output folder: {config.OUTPUT_FOLDER_PATH}")
    print()
    
    feedback = extract_feedback(date_str)
    
    if feedback is None or len(feedback) == 0:
        print("No feedback data to save.")
        return
    
    save_feedback(feedback)
    print("\nDone.")


if __name__ == "__main__":
    main()