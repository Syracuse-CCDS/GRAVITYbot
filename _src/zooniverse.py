"""
zooniverse.py

Single interface for all Zooniverse/Panoptes interactions:
- Posting summaries to Talk forums
- Fetching Talk export data
"""

import datetime
import io
import os
import re
import sys
import tarfile
import urllib.request

import pandas
import panoptes_client

# Add project root to path for config import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config


# Board IDs for different summary types
BOARD_IDS = {
    "talk": 6946,    # Gravity Spy Talk summaries
    "alog": 6945,    # aLOG summaries (LHO/LLO)
}

DISCUSSION_FOOTER = """
NOTICE: Summary created by GRAVITYbot, an LLM powered summarizer maintained by Gravity Spy researchers
and is under construction and is subject to updates in training. Full documentation and development can
be found at the [Syracuse CCDS GitHub](https://github.com/Syracuse-CCDS/GRAVITYbot). Any concerns,
questions, or recommended updates can be directed to the Syracuse Gravity Spy research team.
""".strip().replace("\n", " ")


# -----------------------------------------------------------------------------
# Connection
# -----------------------------------------------------------------------------

def connect():
    """Establishes connection to Panoptes API."""
    panoptes_client.Panoptes.connect(
        username=config.PANOPTES_USER,
        password=config.PANOPTES_PASS
    )


# -----------------------------------------------------------------------------
# Fetching Talk Data
# -----------------------------------------------------------------------------

def fetch_talk_export(data_folder_path=None):
    """
    Downloads and extracts Talk comment data from Zooniverse for the configured project.

    Args:
        data_folder_path (str, optional): Path to folder where Talk data should be stored.
            Defaults to config.DATA_FOLDER_PATH.

    Returns:
        str: The URL of the downloaded Talk export, or None if download failed.

    Notes:
        - Requires valid PANOPTES_USER and PANOPTES_PASS in config.
        - Panoptes limits export generation to once per 24 hours.
        - Extracts tarball and converts JSON to CSV for downstream processing.
    """
    if data_folder_path is None:
        data_folder_path = config.DATA_FOLDER_PATH
    
    # Connect to Panoptes
    try:
        connect()
    except panoptes_client.panoptes.PanoptesAPIException as error:
        print(f"""
!!! PANOPTES API EXCEPTION !!!
Raw Exception Output: "{error}"
    Perhaps you have called talk data more than once in the last 24 hours.
    NOTICE: Panoptes API warnings are not particularly well documented.
    See PANOPTES documentation:
    - https://panoptes-python-client.readthedocs.io/en/latest/panoptes_client.html#panoptes_client.panoptes
    It is not uncommon for data retrieval to fail. Perhaps try again later? 
    Stopping talk data fetch...
    Attempting summary on older data...
        """)
        return None

    # Get project ID from slug
    project = panoptes_client.Project.find(slug=config.PANOPTES_SLUG)
    proj_id = int(str(project).split(' ')[1].split('>')[0])

    # Attempt to get/generate Talk export
    talk_url = None
    try:
        panoptes_client.Project(proj_id).get_export(
            export_type='talk_comments', 
            generate=True, 
            wait=False
        )
        talk_describe = panoptes_client.Project(proj_id).describe_export('talk_comments')
        talk_url = talk_describe['data_requests'][0]['url']
        print(f"Talk export URL: {talk_url}")

    except panoptes_client.panoptes.PanoptesAPIException as error:
        print(f"""
!!! PANOPTES API EXCEPTION !!!
Raw Exception Output: "{error}"
    Perhaps you have called talk data more than once in the last 24 hours.
    NOTICE: Panoptes API warnings are not particularly well documented.
    See PANOPTES documentation:
    - https://panoptes-python-client.readthedocs.io/en/latest/panoptes_client.html#panoptes_client.panoptes
    It is not uncommon for data retrieval to fail. Perhaps try again later? 
    Stopping talk data fetch...
    Attempting summary on older data...
        """)
        return None
    except Exception:
        # Retry with different approach
        try:
            panoptes_client.Project(proj_id).generate_export('talk_comments')
            panoptes_client.Project(proj_id).get_export(export_type='talk_comments')
            talk_describe = panoptes_client.Project(proj_id).describe_export('talk_comments')
            talk_url = talk_describe['data_requests'][0]['url']
            print(f"Talk export URL (retry): {talk_url}")
        except Exception as e:
            print(f"Failed to get Talk export: {e}")

    if talk_url is None:
        print("""
WARNING: Talk description URL is empty.
    Panoptes API did not generate a download URL.
    This may be a Panoptes bug or rate limit.
    Continuing with existing data if available...
        """)
        return None

    # Download and extract tarball
    try:
        talk_response = urllib.request.urlopen(talk_url).read()
        file_obj = io.BytesIO(talk_response)
        
        with tarfile.open(fileobj=file_obj, mode='r:gz') as tar:
            tar.extractall(path=str(data_folder_path))

        # Convert JSON to CSV
        current_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        json_path = f"{data_folder_path}/project-1104-comments_{current_date}.json"
        csv_path = f"{data_folder_path}/project-1104-comments_{current_date}.csv"

        try:
            talk_df = pandas.read_json(json_path)
            talk_df.to_csv(csv_path, index=False)
            print(f"Talk data saved: {csv_path}")
        except FileNotFoundError:
            print(f"Note: Export file not dated today ({current_date}), using existing data.")

    except Exception as e:
        print(f"Failed to download/extract Talk data: {e}")
        return None

    return talk_url


# -----------------------------------------------------------------------------
# Posting Summaries
# -----------------------------------------------------------------------------

def post_summary(summary_type, date_str, title=None, summary_path=None, lab=None):
    """
    Posts a summary to the appropriate Zooniverse Talk forum.

    Args:
        summary_type (str): Type of summary - "talk" or "alog"
        date_str (str): Date string (YYYY-MM-DD) for the summary
        title (str, optional): Custom discussion title. Auto-generated if not provided.
        summary_path (str, optional): Path to summary file. Auto-generated if not provided.
        lab (str, optional): Lab identifier ("LHO" or "LLO") - required for alog summaries

    Raises:
        ValueError: If summary_type is invalid or lab is missing for alog summaries
    """
    if summary_type not in BOARD_IDS:
        raise ValueError(f"Unknown summary type: {summary_type}. Use 'talk' or 'alog'.")
    
    if summary_type == "alog" and not lab:
        raise ValueError("Lab identifier required for alog summaries")
    
    board_id = BOARD_IDS[summary_type]
    
    # Generate default title if not provided
    if title is None:
        if summary_type == "talk":
            title = f"Gravity Spy Talk Summary: {date_str}"
        else:
            title = f"{lab} aLOG Summary: {date_str}"
    
    # Generate default path if not provided
    if summary_path is None:
        if summary_type == "talk":
            summary_path = config.OUTPUT_FOLDER_PATH / f"ZooniverseTalkSummary_{date_str}.md"
        else:
            summary_path = config.OUTPUT_FOLDER_PATH / f"{lab}aLogForumSummary_{date_str}.md"
    
    # Read summary content
    with open(summary_path, "r", encoding="utf-8") as f:
        summary_content = f.read()
    
    # Build discussion body
    body = f"## {title}\n\n{summary_content}\n\n{DISCUSSION_FOOTER}"
    
    # Escape URLs to open in new tab (Zooniverse convention)
    body = re.sub(r"https://", r"+tab+https://", body)
    
    # Build payload
    payload = {
        "discussions": {
            "board_id": board_id,
            "title": title,
            "comments": [{"body": body}]
        }
    }
    
    # Connect and post
    connect()
    
    talk = panoptes_client.panoptes.Talk()
    talk.http_post("discussions", json=payload)
    
    print(f"Posted '{title}' to Zooniverse board {board_id}")


def post_talk_summary(date_str):
    """Convenience function to post a Talk summary."""
    post_summary("talk", date_str)


def post_alog_summary(date_str, lab):
    """Convenience function to post an aLOG summary."""
    post_summary("alog", date_str, lab=lab)