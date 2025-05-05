#####################################################################################################
# DOCUMENTATION NOTES : #############################################################################
# File Creator: Alexander O. Smith (2024-present), aosmith@syr.edu
# Current Maintainer: Alexander O. Smith, aosmith@syr.edu
# Last Update: April 2, 2025
# Program Goal:
# This file is the main alog summary executable Python file of "GRAVITYbot"
#####################################################################################################
#####################################################################################################
# DEPENDENCIES ######################################################################################
# Package Dependencies
import os, sys, re, csv, openai, pytz, smtplib, ssl
from datetime import datetime, timezone, date, timedelta
import pandas as pd
# API Imports
from openai import OpenAI
from panoptes_client import Panoptes
# Local enviornment imports and path appends
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dotenv import find_dotenv, load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../_data')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../_output')))
import prompts, alog, emails, alogPosts

## ----------------------
## Monkey Patch print() for better debugging
## it would probably be better to use logging, but this is easier for now.
## ----------------------
_print=print
def print(*args, **kwargs):
    # Add a timestamp to the print function
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Call the original print function with the timestamp
    _print(f"{__file__}[{timestamp}] ", *args, **kwargs)
## ----------------------


# Example of how to import a prompt from prompts py file.
#####################################################################################################
# Functions #########################################################################################
# 0. start_end_dates    :   produces two adjacent weeks spans
# 1. load_alog          :   loads alog data
# 2. segment_by_time    :   limits alog data to those within particular dates
# 3. chat_with_gpt4     :   calls chatGPT4 bot (more expensive, higher input rate limit)
# 4. main               :   initiates above functions, and loads prompt file info
#####################################################################################################
## WARNING: This function will need to be rewritten to work explicitly on alog data instead.
# Produces start and end dates for the most recent two weeks of Talk data.
def start_end_dates():
    print('Loading the most recent ALOG forum data...')
    
    # Today's date
    current_date = datetime.now(timezone.utc)

    talk_dat1_start = current_date - timedelta(days=3)
    talk_dat0_end = talk_dat1_start - timedelta(days=1)
    talk_dat0_start = talk_dat0_end - timedelta(days=3)

    # Convert all the dates to strings formatted as the Talk file name conventions.
    talk_dat1_start = talk_dat1_start.strftime('%Y-%m-%d')
    talk_dat0_end = talk_dat0_end.strftime('%Y-%m-%d')
    talk_dat0_start = talk_dat0_start.strftime('%Y-%m-%d')
    talk_dat1_end = current_date.strftime('%Y-%m-%d')
    print(f'Checking for file date: {talk_dat1_end}')

    return {
        'talk_dat1_start'   :   talk_dat1_start, 
        'talk_dat1_end'     :   talk_dat1_end, 
        'talk_dat0_start'   :   talk_dat0_start, 
        'talk_dat0_end'     :   talk_dat0_end 
    }

# Function: loads alog data and gets comments which contain text
def load_alog(file_path):
    talk_url = 'https://www.zooniverse.org/projects/zooniverse/gravity-spy/talk/'
    with open('_data/'+file_path, encoding='utf-8') as file:
        reader = csv.DictReader(file)

        # Define the Universal timezone
        utc = pytz.UTC

        # Set up lists for dataframe return
        txt         =   []
        times       =   []
        comment_urls=   []
        rss_feed    =   []


        for row in reader:

            # Define time formats with and without microseconds
            date_fmt = "%a, %d %b %Y %H:%M:%S %z"

            # Timestamp Data Clean
            timestamp = row['entry_date']

            try:
            # Parse TimeoutError: [Errno 110] Connection timed outthe timestamp
                time = datetime.strptime(timestamp, date_fmt).astimezone(utc)
                times.append(time)
                
            except:
                print(f'Datetime Conversion Warning')
                print(timestamp)
                continue

            text = row['text']
            # I need to clean up text
            text = re.sub(r'https.*\s', ' ', text)
            text = re.sub(r'@\w+', ' ', text)
            text = re.sub(r'Hi,\n|Hello,\n', '' , text, re.IGNORECASE)
            text = re.sub(r'Thanks|Thank you', '', text, re.IGNORECASE)
            text = re.sub(r'[^A-Za-z0-9\>\s\'\"\?\.\!]', ' ', text)
            text = re.sub(r'\.+', ' ', text)
            text = re.sub(r'\s[b-z][\.\s]', ' ', text)
            text = re.sub(r'^v$', '' ,text)
            text = re.sub(r'[\n]', ' ', text)
            text = re.sub(r'[0-9]+\s', ' ', text)
            text = re.sub(r'[a-z][0-9]+', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            txt.append(text)
            #print(txt[0:10])

            url = row['entry_url']
            comment_urls.append(url)

            rss_feed.append(row['rss_url'])
        # Generate DataFrame of data necessary for GRAVITYbot interpretation
        text_dat = pd.DataFrame({
            'timestamp'     : times,
            'comment'       : txt,
            'comment_url'   : comment_urls,
            'rss'           : rss_feed,
        })
        
    return text_dat


# Function: transforms dates to segment questions
def segment_by_time(text_dat, start_date, end_date):
    # Parse and localize start_date and end_date to UTC
    utc = pytz.UTC
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    start_dt = utc.localize(start_dt)
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    end_dt = utc.localize(end_dt)

    # Get the comments and URLs between the date range start_date & end_date
    talk_dat = text_dat[(text_dat['timestamp'] >= start_dt) & (text_dat['timestamp'] <= end_dt)]
    gpt_talk_reduce = talk_dat[['comment', 'comment_url']]
    gpt_talk_str = gpt_talk_reduce.to_string(header = False, index = False)
    gpt_talk_str = re.sub(r'\s+', ' ', gpt_talk_str)
    
    return gpt_talk_str


def chat_with_gpt4(user_prompt, sys_prompt):
    _ = load_dotenv(find_dotenv())
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY")) 
    
    response = client.chat.completions.create(
        # Messages: priming the model for a response
        messages = [
            
            {'role' : 'system', 'content' : sys_prompt},# System "role" in which openAI responds
            {'role': 'user', 'content': user_prompt}    # What "I" am asking/telling the model
            ],
        model="gpt-4-turbo",                            # The openAI model for the project
        temperature=    0.8,                            # Lower = more flexibility, Higher = more accurate
        max_tokens=     4000                            # NOTICE: higher tokens, more money.
    )

    # Outfile of Call and Response to GravitySpy
    current_time = f"{datetime.now()}"
    with open("_output/gravityBot_output.txt", "a") as out_file:
        out_file.write(f"GRAVITYBOT PROMPT TIME: {current_time}\n\n")
        out_file.write(f"SYSTEM PROMPT:\n{sys_prompt}\nUser Prompt: {user_prompt}\n")
        out_file.write(f"GRAVITYBOT RESPONSE:\n{str(response)}\n\n")

    return response.choices[0].message.content


# Main Function: Calls all previous functions for a user specified time frame
def main():
    print("------------------")
    print("Starting ALOG Summary...")
    print("------------------")

    # Retrieve most updated alog data
    alogdata = alog.main()
    print("LIGO Alog Forum Data Request Complete")
    # Get the most recent csv name, and the start and end dates for the most recent two weeks.     
    time_deltas = start_end_dates()

    # Set up talkdata and alogdata file names in a list
    alog_dat = "aLOG_RSS_deduplicated.csv"

    # Load Gravity Spy Talk and alog data files and sort alog
    alogload = load_alog(alog_dat)

    #Filtering alog into two datasets
    lho_alog = "https://alog.ligo-wa.caltech.edu/aLOG/rss-feed.php"
    llo_alog = "https://alog.ligo-la.caltech.edu/aLOG/rss-feed.php"
    lho_load = alogload[alogload['rss'] == lho_alog]
    llo_load = alogload[alogload['rss'] == llo_alog]

    # Call segment_by_time function using the automated start-end days.
    lho_dat0 = segment_by_time(lho_load, time_deltas['talk_dat0_start'], time_deltas['talk_dat0_end']) # Alog Older week
    lho_dat1 = segment_by_time(lho_load, time_deltas['talk_dat1_start'], time_deltas['talk_dat1_end']) # Alog Newer week
    print(f'LHO: first dataset is {str(len(lho_dat0))} strings long and the second is {str(len(lho_dat1))}.')

    llo_dat0 = segment_by_time(llo_load, time_deltas['talk_dat0_start'], time_deltas['talk_dat0_end']) # Alog Older week
    llo_dat1 = segment_by_time(llo_load, time_deltas['talk_dat1_start'], time_deltas['talk_dat1_end']) # Alog Newer week
    print(f'LLO: first dataset is {str(len(llo_dat0))} strings long and the second is {str(len(llo_dat1))}.')

    # Call ex_func_prompt_gen from prompts.py 
    llo_prompt = prompts.alog_prompt(llo_dat0, llo_dat1)
    lho_prompt = prompts.alog_prompt(lho_dat0, lho_dat1)

    print("Summarizing Alogs")
    # Call chatGPT function for ALOG Forum summaries and save them to MD files
    current_day = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    try:
        lloBot = chat_with_gpt4(llo_prompt[0], llo_prompt[1])
        with open(f'./_output/LLOaLogForumSummary_{current_day}.md', 'w') as lloBotResp:
            lloBotResp.write(lloBot)
            lloBotResp.close()
    except:
        print("WARNING: No LLO aLOG Summary file saved.")
    try:
        lhoBot = chat_with_gpt4(lho_prompt[0], lho_prompt[1])
        with open(f'./_output/LHOaLogForumSummary_{current_day}.md', 'w') as lhoBotResp:
            lhoBotResp.write(lhoBot)
            lhoBotResp.close()
    except:
        print("WARNING: No LHO aLOG Summary file saved.")
    alogPosts.alog_discussion_post(current_day)

    print("------------------")
    print("Ending ALOG Summary...")
    print("------------------")

gsBotResponse = main()