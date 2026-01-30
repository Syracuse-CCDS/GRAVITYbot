"""
GRAVITYbot - Talk Summary Script
--------------------------------
Fetches Zooniverse Talk forum data, generates LLM summaries comparing
two consecutive weekly periods, and distributes via email and forum post.

Author: Alexander O. Smith (2024-present)
Maintainer: Alexander O. Smith <aosmith@syr.edu>
"""
import logging
import os
import sys
from datetime import datetime, timezone, timedelta

import pandas as pd
import pytz

# Add project root to path for config import
# TODO: Remove when proper packaging is implemented
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
import emails
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
# Board IDs to exclude from summaries (GRAVITYbot's own board)
EXCLUDED_BOARD_IDS = [6872]

# User IDs to exclude (GRAVITYbot's own posts to prevent circular summaries)
EXCLUDED_USER_IDS = [2877652]

# Time window configuration
PERIOD_DAYS = 7
GAP_DAYS = 1  # Gap between prior and current period


def get_date_ranges(df=None):
    """
    Calculate date ranges for the two comparison periods.
    
    Args:
        df: Optional DataFrame with 'timestamp' column. If provided (dry run mode),
            calculates ranges based on actual data. Otherwise uses current date.
    
    Returns:
        dict with prior_start, prior_end, current_start, current_end (YYYY-MM-DD strings)
    """
    if df is not None and not df.empty:
        # Use actual data range (for dry run with old data)
        latest = df['timestamp'].max()
        current_end = latest
    else:
        current_end = datetime.now(timezone.utc)
    
    current_start = current_end - timedelta(days=PERIOD_DAYS - 1)
    prior_end = current_start - timedelta(days=GAP_DAYS)
    prior_start = prior_end - timedelta(days=PERIOD_DAYS - 1)
    
    return {
        'current_start': current_start.strftime('%Y-%m-%d'),
        'current_end': current_end.strftime('%Y-%m-%d'),
        'prior_start': prior_start.strftime('%Y-%m-%d'),
        'prior_end': prior_end.strftime('%Y-%m-%d'),
    }


def load_talk_data(file_path):
    """
    Load and preprocess Talk forum data.
    
    Args:
        file_path: Path to the Talk export CSV
        
    Returns:
        DataFrame with timestamp, comment, and comment_url columns
    """
    talk_url = 'https://www.zooniverse.org/projects/zooniverse/gravity-spy/talk/'
    
    df = pd.read_csv(file_path, encoding='utf8')
    
    # Filter out GRAVITYbot's board and user to prevent circular summaries
    df = df[~df.board_id.isin(EXCLUDED_BOARD_IDS)]
    df = df[~df.comment_user_id.isin(EXCLUDED_USER_IDS)]
    
    return pd.DataFrame({
        'timestamp': pd.to_datetime(df['comment_created_at'], utc=True, format='mixed'),
        'comment': df['comment_body'].fillna('').apply(utils.clean_talk_text),
        'comment_url': df.apply(
            lambda row: f"{talk_url}{row['board_id']}/{row['discussion_id']}", 
            axis=1
        ),
    })


def filter_by_date_range(df, start_date, end_date):
    """
    Filter DataFrame to a date range.
    
    Args:
        df: DataFrame with 'timestamp' column
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        
    Returns:
        Filtered DataFrame with comment and comment_url columns
    """
    start_dt = pytz.UTC.localize(datetime.strptime(start_date, '%Y-%m-%d'))
    end_dt = pytz.UTC.localize(datetime.strptime(end_date, '%Y-%m-%d'))
    
    filtered = df[(df['timestamp'] >= start_dt) & (df['timestamp'] <= end_dt)]
    
    return filtered[['comment', 'comment_url']]


def main():
    """Run the Talk summary pipeline."""
    logger.info("------------------")
    logger.info("Starting Talk summary...")
    if config.DRY_RUN:
        logger.info("DRY RUN MODE - No emails or posts will be sent")
    logger.info("------------------")

    current_day = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    # Fetch data (or use existing in dry run mode)
    if config.DRY_RUN:
        csv_path = config.DATA_FOLDER_PATH / zooniverse.TALK_EXPORT_FILENAME
        if not csv_path.exists():
            logger.error(f"DRY RUN: No existing data at {csv_path}")
            return
        logger.info(f"DRY RUN: Using existing data from {csv_path}")
    else:
        csv_path = zooniverse.fetch_talk_export()
        if csv_path is None:
            logger.error("Cannot proceed without Talk data")
            return
        logger.info("Talk forum data fetch complete")

    # Load and filter data
    talk_data = load_talk_data(csv_path)

    # Calculate date ranges for comparison
    # In dry run mode, use actual data range instead of current date
    date_ranges = get_date_ranges(talk_data if config.DRY_RUN else None)
    logger.info(
        f"Comparing periods: {date_ranges['prior_start']} to {date_ranges['prior_end']} "
        f"vs {date_ranges['current_start']} to {date_ranges['current_end']}"
    )
    
    prior_data = filter_by_date_range(
        talk_data, 
        date_ranges['prior_start'], 
        date_ranges['prior_end']
    )
    current_data = filter_by_date_range(
        talk_data, 
        date_ranges['current_start'], 
        date_ranges['current_end']
    )
    
    logger.info(f"Talk: {len(prior_data)} prior records, {len(current_data)} current records")

    # Generate LLM summary
    user_prompt, system_prompt = prompts.talk_prompt(prior_data, current_data)
    
    try:
        summary = llm_client.generate(user_prompt, system_prompt, log_file="llm_talk.log")
    except llm_client.LLMError as e:
        logger.error(f"LLM generation failed: {e}")
        return

    # Save debug copy (overwritten each run, not for reloading)
    debug_path = config.OUTPUT_FOLDER_PATH / "last_talk_summary.md"
    debug_path.write_text(summary, encoding='utf-8')
    logger.debug(f"Debug copy saved to {debug_path}")

    # Distribute summary
    if config.DRY_RUN:
        logger.info("DRY RUN: Skipping email and Zooniverse post")
        logger.info(f"Summary preview ({len(summary)} chars):\n{summary[:500]}...")
    else:
        logger.info("Sending email...")
        try:
            emails.send_talk_summary_email(current_day, summary)
        except Exception as e:
            logger.warning(f"Email failed: {e}")
        
        logger.info("Posting to Zooniverse Talk...")
        try:
            zooniverse.post_talk_summary(current_day, summary)
        except Exception as e:
            logger.warning(f"Zooniverse post failed: {e}")

    logger.info("------------------")
    logger.info("Talk summary complete")
    logger.info("------------------")


if __name__ == "__main__":
    main()