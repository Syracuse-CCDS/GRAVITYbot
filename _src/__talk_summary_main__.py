#####################################################################################################
# DOCUMENTATION NOTES : #############################################################################
# File Creator: Alexander O. Smith (2024-present), aosmith@syr.edu
# Current Maintainer: Alexander O. Smith, aosmith@syr.edu
# Last Update: July 15, 2025
# Program Goal:
# This file is the main talk summary executable Python file of "GRAVITYbot"
#####################################################################################################
#####################################################################################################
# DEPENDENCIES ######################################################################################
import os
import sys
import re
import pytz
from datetime import datetime, timezone, timedelta

import pandas as pd

# Add project root to path for config import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
import prompts
import emails
import llm_client
import utils
import zooniverse

## ----------------------
## Monkey Patch print() for better debugging
## TODO: Replace with proper logging
## ----------------------
_print = print
def print(*args, **kwargs):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _print(f"{os.path.basename(__file__)}[{timestamp}] ", *args, **kwargs)
## ----------------------

#####################################################################################################
# Functions #########################################################################################

def start_end_dates():
    """Produces start and end dates for the most recent two weeks of Talk data."""
    print('Loading the most recent Talk forum data...')
    current_date = datetime.now(timezone.utc)
    talk_file = ''

    while len(talk_file) < 1:
        talk_dat1_start = current_date - timedelta(days=7)
        talk_dat0_end = talk_dat1_start - timedelta(days=1)
        talk_dat0_start = talk_dat0_end - timedelta(days=7)

        talk_dat1_start = talk_dat1_start.strftime('%Y-%m-%d')
        talk_dat0_end = talk_dat0_end.strftime('%Y-%m-%d')
        talk_dat0_start = talk_dat0_start.strftime('%Y-%m-%d')
        talk_dat1_end = current_date.strftime('%Y-%m-%d')
        print(f'Checking for file date: {talk_dat1_end}')

        file_search = os.listdir(config.DATA_FOLDER_PATH)
        for f in file_search:
            if re.match(f'project-1104-comments_{talk_dat1_end}.csv', f):
                talk_file = f
                print(f'NOTICE: Talk file "{talk_file}" found!\n    Generating date range for summary...\n')

        if talk_dat0_start == '2009-12-12':
            print("""
DATA ISSUE: It appears current Talk Data needs to be imported to the data directory.

TROUBLESHOOTING SUGGESTIONS:
    1. Make sure __main__.main() is running load_text(file_path) with the expected talk data file path.
    2. Make sure the proper panoptes credentials are configured in the .env file.
    3. Ask the Zooniverse project owner for proper panoptes credentials rights to download data.
    4. Check whether the Zooniverse "slug" in dotenv is correct.
    5. Troubleshoot talk_data.py.
            """)
            break

        current_date -= timedelta(days=1)

    return {
        'talk_file': talk_file,
        'talk_dat1_start': talk_dat1_start,
        'talk_dat1_end': talk_dat1_end,
        'talk_dat0_start': talk_dat0_start,
        'talk_dat0_end': talk_dat0_end
    }


def load_talk(file_path):
    """Loads Talk data and gets comments which contain text."""
    talk_url = 'https://www.zooniverse.org/projects/zooniverse/gravity-spy/talk/'

    reader = pd.read_csv(file_path, encoding='utf8')

    # Drop rows with board_ids associated with GRAVITYbot to reduce circularity in summaries
    drop_board = [6872]
    reader = reader[~reader.board_id.isin(drop_board)]
    
    # Drop GRAVITYbot user_id
    # NOTE: Hardcoded because dynamic lookup caused issues (see original comments)
    drop_gb = [2877652]
    reader = reader[~reader.comment_user_id.isin(drop_gb)]

    utc = pytz.UTC

    timestamp = reader['comment_created_at']
    times = pd.to_datetime(timestamp, utc=True, format='mixed', errors='raise')
    comment_urls = reader.apply(
        lambda row: f"{talk_url}{row['board_id']}/{row['discussion_id']}", axis=1)
    text = reader['comment_body'].fillna('').apply(utils.clean_talk_text)

    text_dat = pd.DataFrame({
        'timestamp': times,
        'comment': text,
        'comment_url': comment_urls,
    })

    return text_dat


def segment_by_time(text_dat, start_date, end_date):
    """Filters data to a specific date range and formats for LLM input."""
    utc = pytz.UTC
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    start_dt = utc.localize(start_dt)
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    end_dt = utc.localize(end_dt)

    talk_dat = text_dat[(text_dat['timestamp'] >= start_dt) & (text_dat['timestamp'] <= end_dt)]
    gpt_talk_reduce = talk_dat[['comment', 'comment_url']]
    gpt_talk_str = gpt_talk_reduce.to_string(header=False, index=False)
    gpt_talk_str = re.sub(r'\s+', ' ', gpt_talk_str)

    return gpt_talk_str


def chat_with_gpt4(user_prompt, sys_prompt):
    """Calls Azure OpenAI for summarization."""
    client = llm_client.LLMClient().initialize()

    response = client.generate(
        messages=[
            {'role': 'system', 'content': sys_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        temperature=0.8,
        max_tokens=4000
    )

    current_time = f"{datetime.now()}"
    log_path = config.OUTPUT_FOLDER_PATH / "gravityBot_output.txt"
    with open(log_path, "a") as out_file:
        out_file.write(f"GRAVITYBOT PROMPT TIME: {current_time}\n\n")
        out_file.write(f"SYSTEM PROMPT:\n{sys_prompt}\nUser Prompt: {user_prompt}\n")
        out_file.write(f"GRAVITYBOT RESPONSE:\n{response}\n\n")

    return response


def main():
    print("------------------")
    print("Starting talk summary...")
    if config.DRY_RUN:
        print("DRY RUN MODE - No emails or posts will be sent")
    print("------------------")

    current_day = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    # Get Talk Data from Panoptes API
    zooniverse.fetch_talk_export()
    print("GravitySpy Talk Forum Data Request Complete")

    # Get the most recent csv name and date ranges
    time_deltas = start_end_dates()

    # Load Gravity Spy Talk data file
    talkload = load_talk(config.DATA_FOLDER_PATH / time_deltas['talk_file'])

    # Segment by time for the two week periods
    talk_dat0 = segment_by_time(talkload, time_deltas['talk_dat0_start'], time_deltas['talk_dat0_end'])
    talk_dat1 = segment_by_time(talkload, time_deltas['talk_dat1_start'], time_deltas['talk_dat1_end'])

    # Generate prompts
    talk_prompt = prompts.ligo_prompt(talk_dat0, talk_dat1)

    # Call LLM for Zooniverse Talk summary
    try:
        gsBot = chat_with_gpt4(talk_prompt[0], talk_prompt[1])
        summary_path = config.OUTPUT_FOLDER_PATH / f"ZooniverseTalkSummary_{current_day}.md"
        with open(summary_path, 'w') as gsBotResp:
            gsBotResp.write(gsBot)
    except Exception as e:
        print(f"WARNING: No Zooniverse Talk Summary file saved. Error: {e}")
        return

    # Send email and post to Zooniverse Talk
    if config.DRY_RUN:
        print("DRY RUN: Skipping email and Zooniverse Talk post")
    else:
        print("Sending email...")
        try:
            emails.send_talk_summary_email(current_day)
        except Exception as e:
            print(f"WARNING: Email failed to send. Error: {e}")
        
        print("Posting to Zooniverse Talk...")
        try:
            zooniverse.post_talk_summary(current_day)
        except Exception as e:
            print(f"WARNING: Zooniverse post failed. Error: {e}")

    print("------------------")
    print("Talk summary complete")
    print("------------------")


if __name__ == "__main__":
    main()