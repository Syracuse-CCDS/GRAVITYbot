"""
GRAVITYbot - aLOG Summary Script
--------------------------------
This script serves as the main executable for GRAVITYbot, a system that fetches,
parses, summarizes, and posts LIGO aLOG data to the Zooniverse Talk forum.

Author: Alexander O. Smith (2024–present)
Maintainer: Alexander O. Smith <aosmith@syr.edu>
"""

# Standard Library
import csv
import datetime
import os
import pathlib
import re

# Third-party Libraries
import dotenv
import openai
import pandas
import panoptes_client
import pytz

# Local Modules
import alog
import llm_prompts

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

    return  {
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


def clean_comment_text(text):
    """
    Cleans and normalizes a comment text by removing URLs, mentions, greetings,
    thanks, unwanted punctuation, and extra whitespace.

    Args:
        text (str): The raw comment text to clean.

    Returns:
        str: The cleaned and normalized comment text.
    
    Behavior:
        - Removes URLs starting with 'https' up to the next whitespace.
        - Removes Twitter-style mentions (e.g., @username).
        - Removes greetings like 'Hi,' or 'Hello,' (case-insensitive).
        - Removes gratitude phrases like 'Thanks' or 'Thank you' (case-insensitive).
        - Removes any character not alphanumeric or common punctuation (?, !, ., >, quotes).
        - Collapses repeated periods into single spaces.
        - Removes standalone single letters b-z surrounded by spaces or dots.
        - Removes isolated lowercase 'v'.
        - Replaces newline characters with spaces.
        - Collapses multiple whitespace into single spaces.
    """

    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"Hi,\n|Hello,\n", "" , text, re.IGNORECASE)
    text = re.sub(r"Thanks|Thank you", "", text, re.IGNORECASE)
    text = re.sub(r"[^A-Za-z0-9>\s'\"?.!]", " ", text)
    text = re.sub(r"\.+", " ", text)
    text = re.sub(r"\s[b-z][.\s]", " ", text)
    text = re.sub(r"^v$", "" ,text)
    text = re.sub(r"[\n]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_log_data(alog_data_file_path):
    """
    Parses aLOG CSV data and returns separate DataFrames for LHO and LLO entries.

    Args:
        alog_data_file_path (str): Path to the aLOG CSV file containing log entries.

    Returns:
        tuple: Two pandas DataFrames:
            - The first contains entries from the LIGO Hanford Observatory (LHO).
            - The second contains entries from the LIGO Livingston Observatory (LLO).

    Notes:
        - Entries are filtered by RSS URL to distinguish between LHO and LLO.
        - Dates are parsed into UTC timezone-aware datetime objects.
        - Malformed dates are skipped with a warning.
        - Each log entry includes: timestamp, RSS URL, comment URL, title, and cleaned comment text.
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
                "comment": clean_comment_text(row["text"]),
            }

            ## Append the row to the correct list based on rss url
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

    Notes:
        - Uses a lab-specific GPT-4 prompt to generate the summary.
        - Any errors during prompt construction, model call, or file writing are caught and reported.
    """

    print(f"Summarizing {lab} aLOGs.")

    try:
        user_prompt, sys_prompt = llm_prompts.alog_prompt(prior_df, current_df, lab)
        chat_response = chat_with_gpt4(user_prompt, sys_prompt)
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

    output_folder_path = os.environ["GRAVITYBOT_OUTPUT_FOLDER_PATH"]

    columns_to_project = ["comment_url", "comment_title", "comment"]
    prior_period_start, prior_period_end = date_ranges["prior_period_start"], date_ranges["prior_period_end"]
    current_period_start, current_period_end = date_ranges["current_period_start"], date_ranges["current_period_end"]
    output_file = f"{output_folder_path}/{lab}aLogForumSummary_{current_period_end}.md"

    data_prior = filter_by_date_range(data, prior_period_start, prior_period_end)[columns_to_project]
    data_current = filter_by_date_range(data, current_period_start, current_period_end)[columns_to_project]
    print(f"{lab}: prior log records {len(data_prior)} current log records {len(data_current)}.")

    if summarize_logs(data_prior, data_current, lab, output_file):
        post_to_zooniverse(lab, current_period_end, output_file)


def fetch_logs_from_zooniverse():
    data_folder_path = os.environ["GRAVITYBOT_DATA_FOLDER_PATH"]
    expected_result_file_path = f"{data_folder_path}/aLOG_RSS_deduplicated.csv"

    ## --------------------
    ## Retrieve most updated aLOG data
    ## --------------------
    print("LIGO aLOG Forum Data Requested")
    _ = alog.main(data_folder_path)
    print("LIGO aLOG Forum Data Request Complete")
    ## --------------------

    return expected_result_file_path


def chat_with_gpt4(user_prompt, sys_prompt):
    """
    Sends a prompt to OpenAI's GPT-4 Turbo model and returns the generated response.

    Args:
        user_prompt (str): The main user message or question.
        sys_prompt (str): The system message to define assistant behavior or context.

    Returns:
        str: The assistant's reply as a string.

    Notes:
        - Uses the GPT-4 Turbo model via the OpenAI SDK.
        - Temperature controls randomness: lower = more deterministic, higher = more diverse.
        - Token usage affects cost; be mindful of the `max_tokens` parameter.
        - Requires the environment variable 'OPENAI_API_KEY' to be set.
    """

    model = "gpt-4-turbo"
    temperature = 0.8
    max_tokens = 4096

    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    messages = [
        {"role": "system", "content": sys_prompt}, # System "role" in which openAI responds
        {"role": "user", "content": user_prompt}   # What "I" am asking/telling the model
    ]

    response = client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )

    return response.choices[0].message.content


def post_to_zooniverse(lab, day_string, aLog_summary_file_path):
    """
    Posts an aLog summary as a discussion to the Zooniverse Talk forum for a specific lab.

    Args:
        lab (str): The name of the lab (e.g., 'LHO' or 'LLO') for which the summary is being posted.
        day_string (str): The date string representing the summary's day (e.g., '2025-06-25').
        aLog_summary_file_path (str): File path to the pre-generated summary text (Markdown).

    Environment Variables Required:
        PANOPTES_USER: Zooniverse username for API authentication.
        PANOPTES_PASS: Corresponding password.
        PANOPTES_ID: User ID (currently unused, but retrieved).

    Behavior:
        - Reads the summary file and appends a GRAVITYbot footer.
        - Escapes URLs for browser behavior by prepending '+tab+'.
        - Constructs a discussion payload for Zooniverse Talk.
        - Authenticates with the Panoptes client.
        - Prepares the discussion for posting (currently commented out).

    Notes:
        - The actual API call to post (`http_post`) is currently commented out.
        - The board_id is hardcoded as 6945, which should be changed if posting to a different board.
    """

    username = os.environ.get("PANOPTES_USER")
    password = os.environ.get("PANOPTES_PASS")
    user_id = os.environ.get("PANOPTES_ID")  # Currently unused
    board_id = 6945

    discussion_footer = """
NOTICE: Summary created by GRAVITYbot, an LLM powered summarizer maintained by Gravity Spy researchers
and is under construction and is subject to updates in training. Full documentation and development can
be found at the [Syracuse CCDS GitHub](https://github.com/Syracuse-CCDS/GRAVITYbot). Any concerns,
questions, or recommended updates can be directed to the Syracuse Gravity Spy research team.
    """.strip().replace("\n", " ")

    discussion_title = f"{lab} aLOG Summary: {day_string}"
    discussion_text = f"## {discussion_title}\n\n"
    with open(aLog_summary_file_path, "r", encoding="utf-8") as file:
        discussion_text += file.read()
    discussion_text += f"\n\n {discussion_footer}"
    discussion_text = re.sub(r"https://", r"+tab+https://", discussion_text)

    discussion = {
        "discussions": {
            "board_id": board_id,
            "title": discussion_title,
            "comments": [
                {"body": discussion_text}
            ]
        }
    }

    panoptes_client.panoptes.Panoptes.connect(username=username, password=password)
    talk = panoptes_client.panoptes.Talk()
    talk.http_post("discussions", json=discussion)


def main(reference_date):
    """
    Orchestrates the end-to-end workflow for fetching, parsing, and processing aLOG data.

    Args:
        reference_date (datetime): The reference date used to determine the date ranges for log processing.

    Workflow:
        1. Fetches the latest aLOG data file from Zooniverse into a local data folder.
        2. Parses the downloaded log data into separate DataFrames for LHO and LLO labs.
        3. Calculates date ranges based on the given reference date.
        4. Processes lab-specific logs for both LHO and LLO using the calculated date ranges.

    Notes:
        - Assumes supporting functions `fetch_logs_from_zooniverse`, `parse_log_data`,
          `get_date_ranges`, and `process_lab_specific_logs` are implemented elsewhere.
        - Designed to be the main entry point when running the script.
    """

    ## --------------------
    ## Make sure we have the latest alog data data from zooniverse
    ## --------------------
    alog_data_file_path = fetch_logs_from_zooniverse()
    ## --------------------

    ## --------------------
    ## filter logs into lab specific data
    ## --------------------
    lho_data, llo_data = parse_log_data(alog_data_file_path)
    ## --------------------

    date_ranges = get_date_ranges(reference_date)
    process_lab_specific_logs("LHO", lho_data, date_ranges)
    process_lab_specific_logs("LLO", llo_data, date_ranges)


if __name__ == "__main__":
    _ = dotenv.load_dotenv(dotenv.find_dotenv())

    ## ----------------------
    ## Establish pathing to data and output folders
    ## This should likely be done via the config 
    ## ----------------------
    script_path = pathlib.Path(__file__).resolve()
    project_root_folder = script_path.parent.parent
    data_folder_path = (project_root_folder / "_data").resolve()
    output_folder_path = (project_root_folder / "_output").resolve()
    os.environ["GRAVITYBOT_DATA_FOLDER_PATH"] = str(data_folder_path)
    os.environ["GRAVITYBOT_OUTPUT_FOLDER_PATH"] = str(output_folder_path)
    print(f"Path to data folder..: {os.environ['GRAVITYBOT_DATA_FOLDER_PATH']}")
    print(f"Path to output folder: {os.environ['GRAVITYBOT_OUTPUT_FOLDER_PATH']}")
    ## ----------------------

    ## ----------------------
    ## Monkey Patch print() for better debugging
    ## it would probably be better to use logging, but this is easier for now.
    ## ----------------------
    _print=print
    def print(*args, **kwargs):
        script_path = os.path.basename(__file__)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _print(f"{script_path}[{timestamp}] ", *args, **kwargs)
    ## ----------------------

    ## --------------------
    ## Testing: Override methods so they don't do stuff
    ## --------------------
    os.environ["GRAVITYBOT_OUTPUT_TESTING"] = "True"
    if os.environ.get("GRAVITYBOT_OUTPUT_TESTING", "False").lower() == "true":
        print("Non-Destructive Testing...")

        def filter_by_date_range(df, start_date, end_date):
            return df.sample(n=10)

        def fetch_logs_from_zooniverse():
            data_folder_path = os.environ["GRAVITYBOT_DATA_FOLDER_PATH"]
            expected_result_file_path = f"{data_folder_path}/aLOG_RSS_deduplicated.csv"

            print("LIGO aLOG Forum Data Requested")
            print("LIGO aLOG Forum Data Request Complete")
            return expected_result_file_path

        def post_to_zooniverse(lab, day_string, aLog_summary_file_path):
            pass
    ## --------------------

    utc_now = datetime.datetime.now(datetime.timezone.utc)
    main(utc_now)