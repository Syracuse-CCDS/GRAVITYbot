"""
GRAVITYbot - aLOG Summary Script
--------------------------------
Fetches LIGO aLOG data, generates LLM summaries comparing two consecutive
5-day periods for each observatory (LHO/LLO), and posts to Zooniverse Talk.

Author: Alexander O. Smith (2024-present)
Maintainer: Alexander O. Smith <aosmith@syr.edu>
"""
import csv
import datetime
import logging
import os
import sys

import pandas as pd
import pytz

# Add project root to path for config import
# TODO: Remove when proper packaging is implemented
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import alog_feed
import config
import llm_client
import prompts
import utils
import zooniverse

# ---------------------
# Logging Setup
# ---------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ---------------------
# Constants
# ---------------------
PERIOD_DAYS = 5
GAP_DAYS = 1

RSS_URLS = {
    "LHO": "https://alog.ligo-wa.caltech.edu/aLOG/rss-feed.php",
    "LLO": "https://alog.ligo-la.caltech.edu/aLOG/rss-feed.php",
}


def get_date_ranges(period_end_date):
    """
    Generate date ranges for the two most recent periods.
    
    Args:
        period_end_date: datetime marking the end of the current period
        
    Returns:
        dict with prior_period_start/end and current_period_start/end (YYYY-MM-DD strings)
    """
    date_fmt = "%Y-%m-%d"
    
    current_start = period_end_date - datetime.timedelta(days=PERIOD_DAYS - 1)
    prior_end = current_start - datetime.timedelta(days=GAP_DAYS)
    prior_start = prior_end - datetime.timedelta(days=PERIOD_DAYS - 1)
    
    return {
        "prior_period_start": prior_start.strftime(date_fmt),
        "prior_period_end": prior_end.strftime(date_fmt),
        "current_period_start": current_start.strftime(date_fmt),
        "current_period_end": period_end_date.strftime(date_fmt),
    }


def get_latest_timestamp(lab_data):
    """
    Find the most recent timestamp across all labs.
    
    Args:
        lab_data: dict mapping lab name to DataFrame with 'timestamp' column
        
    Returns:
        datetime of the most recent entry, or None if no data
    """
    timestamps = []
    for df in lab_data.values():
        if not df.empty and 'timestamp' in df.columns:
            timestamps.append(df['timestamp'].max())
    
    return max(timestamps) if timestamps else None


def filter_by_date_range(df, start_date, end_date):
    """
    Filter DataFrame to rows within a date range.
    
    Args:
        df: DataFrame with timezone-aware 'timestamp' column
        start_date: Start date string (YYYY-MM-DD), inclusive
        end_date: End date string (YYYY-MM-DD), inclusive
        
    Returns:
        Filtered DataFrame
    """
    start_dt = pytz.UTC.localize(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
    end_dt = pytz.UTC.localize(datetime.datetime.strptime(end_date, "%Y-%m-%d"))
    return df[df["timestamp"].between(start_dt, end_dt)]


def parse_alog_csv(file_path):
    """
    Parse aLOG CSV and separate by observatory.
    
    Args:
        file_path: Path to the aLOG CSV file
        
    Returns:
        dict mapping lab name ("LHO", "LLO") to DataFrame
    """
    date_fmt = "%a, %d %b %Y %H:%M:%S %z"
    
    records = {"LHO": [], "LLO": []}
    
    with open(file_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            # Skip embedded header rows (legacy data artifact)
            if row["entry_date"] == "entry_date":
                continue
                
            try:
                timestamp = datetime.datetime.strptime(
                    row["entry_date"], date_fmt
                ).astimezone(pytz.UTC)
            except ValueError:
                logger.warning(f"Skipping row with unparseable date: {row['entry_date']}")
                continue
            
            # Determine which lab this entry belongs to
            rss_url = row["rss_url"]
            lab = None
            for lab_name, url in RSS_URLS.items():
                if rss_url == url:
                    lab = lab_name
                    break
            
            if lab is None:
                logger.warning(f"Skipping row with unknown RSS URL: {rss_url}")
                continue
            
            records[lab].append({
                "timestamp": timestamp,
                "comment_url": row["entry_url"],
                "comment_title": row["entry_title"],
                "comment": utils.clean_alog_text(row["text"]),
            })
    
    return {lab: pd.DataFrame(data) for lab, data in records.items()}


def summarize_lab(lab, data, date_ranges) -> str | None:
    """
    Generate summary for a single lab.
    
    Args:
        lab: Lab identifier ("LHO" or "LLO")
        data: DataFrame with aLOG entries for this lab
        date_ranges: dict with period start/end dates
        
    Returns:
        Summary string if successful, None otherwise
    """
    columns = ["comment_url", "comment_title", "comment"]
    
    prior_data = filter_by_date_range(
        data, 
        date_ranges["prior_period_start"], 
        date_ranges["prior_period_end"]
    )[columns]
    
    current_data = filter_by_date_range(
        data,
        date_ranges["current_period_start"],
        date_ranges["current_period_end"]
    )[columns]
    
    logger.info(f"{lab}: {len(prior_data)} prior records, {len(current_data)} current records")
    
    try:
        user_prompt, system_prompt = prompts.alog_prompt(prior_data, current_data, lab)
        summary = llm_client.generate(user_prompt, system_prompt)
        logger.info(f"{lab} summary generated ({len(summary)} chars)")
        return summary
        
    except llm_client.LLMError as e:
        logger.error(f"{lab} summary generation failed: {e}")
        return None


def fetch_alog_data():
    """
    Fetch latest aLOG data.
    
    Returns:
        Path to the CSV file, or None if fetch failed
    """
    logger.info("Fetching aLOG data...")
    result = alog_feed.fetch_alog_entries(config.DATA_FOLDER_PATH)
    if result:
        logger.info("aLOG data fetch complete")
    return result


def main(reference_date):
    """
    Run the aLOG summary pipeline.
    
    Args:
        reference_date: datetime used as the end of the current period
    """
    logger.info("------------------")
    logger.info("Starting aLOG summary...")
    if config.DRY_RUN:
        logger.info("DRY RUN MODE - No Zooniverse posts will be made")
    logger.info("------------------")
    
    # Fetch data (or use existing in dry run mode)
    if config.DRY_RUN:
        alog_file = config.DATA_FOLDER_PATH / alog_feed.ALOG_EXPORT_FILENAME
        if not alog_file.exists():
            logger.error(f"DRY RUN: No existing data at {alog_file}")
            return
        logger.info(f"DRY RUN: Using existing data from {alog_file}")
    else:
        alog_file = fetch_alog_data()
        if alog_file is None:
            logger.error("Cannot proceed without aLOG data")
            return
    
    lab_data = parse_alog_csv(alog_file)
    
    # In dry run mode, use actual data range instead of current date
    if config.DRY_RUN:
        latest = get_latest_timestamp(lab_data)
        if latest is None:
            logger.error("DRY RUN: No timestamped data found")
            return
        reference_date = latest
        logger.info(f"DRY RUN: Using data-derived reference date: {reference_date}")
    
    date_ranges = get_date_ranges(reference_date)
    logger.info(
        f"Processing periods: {date_ranges['prior_period_start']} to {date_ranges['prior_period_end']} "
        f"vs {date_ranges['current_period_start']} to {date_ranges['current_period_end']}"
    )
    
    # Process each lab
    for lab in ["LHO", "LLO"]:
        if lab_data[lab].empty:
            logger.warning(f"No data for {lab}, skipping")
            continue
        
        summary = summarize_lab(lab, lab_data[lab], date_ranges)
        
        if summary is None:
            continue
        
        # Save debug copy (overwritten each run, not for reloading)
        debug_path = config.OUTPUT_FOLDER_PATH / f"last_{lab.lower()}_alog_summary.md"
        debug_path.write_text(summary, encoding='utf-8')
        logger.debug(f"Debug copy saved to {debug_path}")
            
        if config.DRY_RUN:
            logger.info(f"DRY RUN: Skipping Zooniverse post for {lab}")
            logger.info(f"{lab} summary preview ({len(summary)} chars):\n{summary[:500]}...")
        else:
            try:
                zooniverse.post_alog_summary(
                    date_ranges["current_period_end"], 
                    summary,
                    lab
                )
            except Exception as e:
                logger.warning(f"Zooniverse post for {lab} failed: {e}")
    
    logger.info("------------------")
    logger.info("aLOG summary complete")
    logger.info("------------------")


if __name__ == "__main__":
    logger.info(f"Data folder: {config.DATA_FOLDER_PATH}")
    logger.info(f"Output folder: {config.OUTPUT_FOLDER_PATH}")
    
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    main(utc_now)