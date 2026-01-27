"""
GRAVITYbot - aLOG Summary Script
--------------------------------
This script serves as the main executable for GRAVITYbot, a system that fetches,
parses, summarizes, and posts LIGO aLOG data to the Zooniverse Talk forum.

Author: Alexander O. Smith (2024–present)
Maintainer: Alexander O. Smith <aosmith@syr.edu>
"""

# Standard Libraries
import csv
import datetime
import os
import sys

# Third-party Libraries
import pandas
import pytz

# Add project root to path for config import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Local Modules
import alog
import config
import llm_client
import prompts
import utils
import zooniverse


def get_date_ranges(current_period_end):
    """
    Generate start and end dates for the two most recent 5-day periods ending at the given datetime.

    Args:
        current_period_end (datetime): The end date of the current 5-day period (inclusive).

    Returns:
        dict: A dictionary containing ISO-formatted date strings:
            - 'prior_period_start' and 'prior_period_end' for the earlier 5-day period
            - 'current_period_start' and 'current_period_end' for the most recent 5-day period

    Notes:
        - Dates are calculated in UTC.
        - Each period spans 5 consecutive days, inclusive of both start and end.
    """
    date_fmt = "%Y-%m-%d"

    current_period_start = current_period_end - datetime.timedelta(days=4)
    prior_period_end = current_period_start - datetime.timedelta(days=1)
    prior_period_start = prior_period_end - datetime.timedelta(days=4)

    return {
        "prior_period_start": prior_period_start.strftime(date_fmt),
        "prior_period_end": prior_period_end.strftime(date_fmt),
        "current_period_start": current_period_start.strftime(date_fmt),
        "current_period_end": current_period_end.strftime(date_fmt)
    }


def filter_by_date_range(df, start_date, end_date):
    """
    Filters a DataFrame to include only rows with timestamps within a specified date range.

    Args:
        df (pd.DataFrame): The input DataFrame containing a 'timestamp' column with timezone-aware datetime values.
        start_date (str): The start date in 'YYYY-MM-DD' format (inclusive).
        end_date (str): The end date in 'YYYY-MM-DD' format (inclusive).

    Returns:
        pd.DataFrame: A filtered DataFrame containing only rows where 'timestamp' falls within the specified range.

    Notes:
        - Both `start_date` and `end_date` are assumed to be in UTC.
        - The 'timestamp' column in `df` must contain timezone-aware datetime objects.
    """
    date_time_format = "%Y-%m-%d"
    start_date_normalized = pytz.UTC.localize(datetime.datetime.strptime(start_date, date_time_format))
    end_date_normalized = pytz.UTC.localize(datetime.datetime.strptime(end_date, date_time_format))
    filtered_data = df[df["timestamp"].between(start_date_normalized, end_date_normalized)]
    return filtered_data


def parse_log_data(alog_data_file_path):
    """
    Parses aLOG CSV data and returns separate DataFrames for LHO and LLO entries.

    Args:
        alog_data_file_path (str): Path to the aLOG CSV file containing log entries.

    Returns:
        tuple: Two pandas DataFrames:
            - The first contains entries from the LIGO Hanford Observatory (LHO).
            - The second contains entries from the LIGO Livingston Observatory (LLO).
    """
    lho_url = "https://alog.ligo-wa.caltech.edu/aLOG/rss-feed.php"
    llo_url = "https://alog.ligo-la.caltech.edu/aLOG/rss-feed.php"
    date_fmt = "%a, %d %b %Y %H:%M:%S %z"

    lho, llo = [], []
    with open(alog_data_file_path, encoding="utf-8") as file_in:
        for row in csv.DictReader(file_in):
            try:
                timestamp = datetime.datetime.strptime(row["entry_date"], date_fmt).astimezone(pytz.UTC)
            except ValueError:
                print(f"Skipping bad date: {row['entry_date']}")
                continue

            clean_row = {
                "timestamp": timestamp,
                "rss": row["rss_url"],
                "comment_url": row["entry_url"],
                "comment_title": row["entry_title"],
                "comment": utils.clean_alog_text(row["text"]),
            }

            (lho if clean_row["rss"] == lho_url else llo if clean_row["rss"] == llo_url else []).append(clean_row)

    return pandas.DataFrame(lho), pandas.DataFrame(llo)


def summarize_logs(prior_df, current_df, lab, output_path):
    """
    Generates a summary of aLOG entries for a specified lab and writes it to a file.

    Args:
        prior_df (pandas.DataFrame): DataFrame containing entries from the prior 5-day period.
        current_df (pandas.DataFrame): DataFrame containing entries from the current 5-day period.
        lab (str): Lab identifier (e.g., "LHO" or "LLO") used for context and labeling.
        output_path (str): File path where the summary should be written.

    Returns:
        bool: True if the summary was successfully generated and saved; False otherwise.
    """
    print(f"Summarizing {lab} aLOGs.")

    try:
        user_prompt, sys_prompt = prompts.alog_prompt(prior_df, current_df, lab)
        chat_response = chat_with_llm(user_prompt, sys_prompt)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(chat_response)
        return True
    except Exception as e:
        print(f"WARNING: No {lab} aLOG Summary saved. Error: {e}")
        return False


def process_lab_specific_logs(lab, data, date_ranges):
    """
    Process and summarize aLOG data for a given lab.

    Args:
        lab (str): Either "LHO" or "LLO".
        data (pd.DataFrame): Parsed aLOG data for the lab.
        date_ranges (dict): Start and end dates for the two recent time windows.
    """
    columns_to_project = ["comment_url", "comment_title", "comment"]
    prior_period_start, prior_period_end = date_ranges["prior_period_start"], date_ranges["prior_period_end"]
    current_period_start, current_period_end = date_ranges["current_period_start"], date_ranges["current_period_end"]
    output_file = config.OUTPUT_FOLDER_PATH / f"{lab}aLogForumSummary_{current_period_end}.md"

    data_prior = filter_by_date_range(data, prior_period_start, prior_period_end)[columns_to_project]
    data_current = filter_by_date_range(data, current_period_start, current_period_end)[columns_to_project]
    print(f"{lab}: prior log records {len(data_prior)} current log records {len(data_current)}.")

    if summarize_logs(data_prior, data_current, lab, output_file):
        if config.DRY_RUN:
            print(f"DRY RUN: Skipping Zooniverse post for {lab}")
        else:
            zooniverse.post_alog_summary(current_period_end, lab)


def fetch_logs_from_zooniverse():
    """Fetches the latest aLOG data from Zooniverse."""
    expected_result_file_path = config.DATA_FOLDER_PATH / "aLOG_RSS_deduplicated.csv"

    print("LIGO aLOG Forum Data Requested")
    _ = alog.main(str(config.DATA_FOLDER_PATH))
    print("LIGO aLOG Forum Data Request Complete")

    return expected_result_file_path


def chat_with_llm(user_prompt, sys_prompt):
    """
    Sends a prompt to Azure OpenAI and returns the generated response.

    Args:
        user_prompt (str): The main user message or question.
        sys_prompt (str): The system message to define assistant behavior or context.

    Returns:
        str: The assistant's reply as a string.
    """
    client = llm_client.LLMClient().initialize()

    response = client.generate(
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.8,
        max_tokens=4096
    )

    return response


def main(reference_date):
    """
    Orchestrates the end-to-end workflow for fetching, parsing, and processing aLOG data.

    Args:
        reference_date (datetime): The reference date used to determine the date ranges for log processing.
    """
    print("------------------")
    print("Starting aLOG summary...")
    if config.DRY_RUN:
        print("DRY RUN MODE - No Zooniverse posts will be made")
    print("------------------")
    
    alog_data_file_path = fetch_logs_from_zooniverse()
    lho_data, llo_data = parse_log_data(alog_data_file_path)

    date_ranges = get_date_ranges(reference_date)
    process_lab_specific_logs("LHO", lho_data, date_ranges)
    process_lab_specific_logs("LLO", llo_data, date_ranges)
    
    print("------------------")
    print("aLOG summary complete")
    print("------------------")


if __name__ == "__main__":
    # Monkey Patch print() for better debugging
    # TODO: Replace with proper logging
    _print = print
    def print(*args, **kwargs):
        script_name = os.path.basename(__file__)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _print(f"{script_name}[{timestamp}] ", *args, **kwargs)

    print(f"Data folder: {config.DATA_FOLDER_PATH}")
    print(f"Output folder: {config.OUTPUT_FOLDER_PATH}")

    utc_now = datetime.datetime.now(datetime.timezone.utc)
    main(utc_now)