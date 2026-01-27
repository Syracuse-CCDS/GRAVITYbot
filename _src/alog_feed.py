"""
alog_feed_parser.py

Original Author:
    Alexander O. Smith <aosmith@syr.edu>

Purpose:
    This script automates the retrieval and preprocessing of aLOG (LIGO Logbook) posts
    from the LHO and LLO RSS feeds. The extracted and cleaned data is intended to
    support downstream analysis and summarization for LIGO's Citizen Science platform
    (e.g., Gravity Spy), helping users identify technical activity and contextual events
    relevant to gravitational wave data quality.

Summary:
    - Pulls recent posts from LHO and LLO aLOG RSS feeds
    - Parses and cleans key metadata, including titles, authors, timestamps, and entry text
    - Exports raw and deduplicated versions of the post set to CSV for further processing

Known Limitations:
    - Currently supports only LIGO (LHO and LLO) RSS feeds; Virgo and KAGRA URLs are noted
      for future implementation but not scraped in this version.
    - Assumes consistent HTML structure in RSS entries; will fail gracefully with warning
      if unexpected formatting occurs.

TODO:
    - Begin prompting for alog
    - Enhance logging and diagnostics
    - Evaluate where and how to call prompt-generating logic
"""

import datetime
import os
import re
import ssl
import sys

import bs4
import feedparser
import pandas

# Add project root to path for config import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

VIRGO_URL = "https://logbook.virgo-gw.eu/virgo/"
KAGRA_URL = "https://klog.icrr.u-tokyo.ac.jp/osl/"
LIGO_RSS_URLS = [
    "https://alog.ligo-wa.caltech.edu/aLOG/rss-feed.php",  # LHO
    "https://alog.ligo-la.caltech.edu/aLOG/rss-feed.php"   # LLO
]

def is_recent(entry_published, time_range):
    """
    Determines whether a given aLOG entry was published within a specified recent time range.

    Args:
        entry_published (str): The publication date string of the entry,
            formatted as "%a, %d %b %Y %H:%M:%S %z" (e.g., "Wed, 26 Jun 2025 10:35:00 +0000").
        time_range (datetime.timedelta): The maximum time delta between today and the entry's date
            for it to be considered recent.

    Returns:
        bool: True if the entry's date falls within the specified time range from today; False otherwise.

    Notes:
        - Only the date component is considered (time is ignored).
        - The input timestamp is converted to a naive datetime (UTC offset is stripped).
        - Today's date is normalized to midnight local time before comparison.
    """

    date_fmt = "%a, %d %b %Y %H:%M:%S %z"
    entry_published = datetime.datetime.strptime(entry_published, date_fmt).replace(tzinfo=None)
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    published_date = entry_published.replace(hour=0, minute=0, second=0, microsecond=0)
    return today - published_date <= time_range


def parse_rss_entry(entry):
    """
    Parses a single RSS feed entry and extracts structured metadata and cleaned text content.

    Args:
        entry (feedparser.FeedParserDict): An individual RSS entry, typically from `feedparser.parse().entries`.

    Returns:
        dict: A dictionary containing the following keys:
            - "entry_title" (str): Title of the RSS entry.
            - "entry_url" (str): URL link to the aLOG report.
            - "rss_url" (str): Base URL of the RSS feed.
            - "entry_date" (str): The publication date of the entry (raw string).
            - "text" (str): Cleaned and normalized body text of the aLOG entry.
            - "tags" (dict): The first tag object from the entry’s tag list (if present).
            - "report_id" (str): Extracted numeric report ID.
            - "author_email" (str): Author’s email address or identifier, extracted from the entry.

    Notes:
        - Uses BeautifulSoup to parse and sanitize HTML content from the `summary` field.
        - Performs text cleanup: removes newlines, tabs, extra punctuation, attached image references, and normalizes whitespace.
        - If any required field is missing or malformed, a warning is printed and an empty dictionary is returned.
    """
    try:
        soup = bs4.BeautifulSoup(entry.summary, "html.parser")

        rep_id = re.sub("Report ID: ", "", soup.find_all("p")[1].text)
        author = re.sub("Author: ", "", soup.p.text)

        txt = soup.get_text(separator=" ")
        txt = re.sub("[\n\t]", "", txt)
        txt = re.sub("[,;]", "", txt)
        txt = re.sub(r"^.*Report ID: \d+ ", "", txt)
        txt = re.sub(" Images attached to this report ", "", txt)
        txt = re.sub(r"\s+", " ", txt)

        return {
            "entry_title": entry.title,
            "entry_url": entry.link,
            "rss_url": entry.title_detail.base,
            "entry_date": entry.published,
            "text": txt,
            "tags": entry.tags[0],
            "report_id": rep_id,
            "author_email": author
        }

    except Exception as e:
        print(f"Warning: Failed to process entry '{entry.title}': {e}")
        return {}


def rss_reduce(feed_url, weeks=2):
    """
    Parses and filters an RSS feed, yielding structured entries published within a recent time window.

    Args:
        feed_url (str): The URL of the RSS feed to parse (e.g., from an aLOG system).
        weeks (int, optional): Number of weeks to look back from today. Defaults to 2.

    Yields:
        dict: Parsed and cleaned RSS entry data (via `parse_rss_entry`) for each entry
        published within the specified time range.

    Notes:
        - Only entries considered "recent" by `is_recent()` are processed.
        - If `parse_rss_entry()` fails or returns an empty result, that entry is skipped.
        - This function uses a generator expression for memory efficiency.
    """

    time_range = datetime.timedelta(weeks=weeks)

    yield from (
        parsed_entry
        for entry
        in feedparser.parse(feed_url).entries
        if is_recent(entry.published, time_range) and (parsed_entry := parse_rss_entry(entry))
    )


def main(data_folder_path):
    """
    Orchestrates the collection, deduplication, and persistence of aLOG RSS feed data.

    Args:
        data_folder_path (str): Path to the folder where aLOG RSS CSV files should be stored.

    Returns:
        pandas.DataFrame: A deduplicated DataFrame of aLOG RSS entries, indexed and ready for downstream processing.

    Workflow:
        1. Optionally bypasses SSL certificate validation (for feeds with expired or self-signed certs).
        2. Iterates over all predefined LIGO RSS feed URLs and gathers recent, valid entries using `rss_reduce()`.
        3. Appends new entries to `aLOG_RSS.csv`, preserving historical feed content.
        4. Deduplicates entries by `report_id` and writes the cleaned data to `aLOG_RSS_deduplicated.csv`.
        5. Prints the number of unique entries and returns the final deduplicated DataFrame.

    Notes:
        - Assumes that `LIGO_RSS_URLS`, `rss_reduce`, and `report_id` fields exist and are valid.
        - If the feed returns malformed or duplicate entries, only the most recent instance per `report_id` is kept.
    """

    ## --------------------
    ## If we might deal with feeds that are self signed or expired
    ## --------------------
    if hasattr(ssl, "_create_unverified_context"):
        ssl._create_default_https_context = ssl._create_unverified_context
    ## --------------------

    aLOG_RSS_path = f"{data_folder_path}/aLOG_RSS.csv"
    aLOG_RSS_deduplicated_path = f"{data_folder_path}/aLOG_RSS_deduplicated.csv"

    feed_entries = []
    for feed_url in LIGO_RSS_URLS:
        feed_entries.extend(rss_reduce(feed_url))

    ## --------------------
    ## Append new feed entries
    ## --------------------
    df = pandas.DataFrame(feed_entries)
    df.to_csv(aLOG_RSS_path, mode="a", header=False, index=False)
    ## --------------------

    ## --------------------
    ## Persist distinct feed entries
    ## --------------------
    df = pandas.read_csv(aLOG_RSS_path).reset_index()
    df = df.drop_duplicates(subset=["report_id"], keep="last")
    df.to_csv(aLOG_RSS_deduplicated_path, index=False)
    ## --------------------

    print(f"Unique alog row count: {len(df)}")

if __name__ == "__main__":
    main(config.DATA_FOLDER_PATH)