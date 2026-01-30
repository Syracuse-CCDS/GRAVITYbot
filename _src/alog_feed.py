"""
alog_feed.py

Retrieves and preprocesses aLOG (LIGO Logbook) posts from LHO and LLO RSS feeds.
Maintains a deduplicated historical archive for summarization and future RAG use.

Raw XML feeds are retained for debugging (overwritten each run).
Canonical CSV grows over time via merge and deduplicate.

Original Author: Alexander O. Smith <aosmith@syr.edu>
"""
import logging
import os
import ssl
import sys
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bs4
import feedparser
import pandas as pd

# Add project root to path for config import
# TODO: Remove when proper packaging is implemented
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ---------------------
# Constants
# ---------------------
LIGO_RSS_URLS = {
    "LHO": "https://alog.ligo-wa.caltech.edu/aLOG/rss-feed.php",
    "LLO": "https://alog.ligo-la.caltech.edu/aLOG/rss-feed.php",
}

# Future expansion
VIRGO_URL = "https://logbook.virgo-gw.eu/virgo/"
KAGRA_URL = "https://klog.icrr.u-tokyo.ac.jp/osl/"

# Output filenames
ALOG_EXPORT_FILENAME = "aLOG_RSS.csv"
ALOG_RAW_FILENAME_TEMPLATE = "aLOG_raw_{lab}.xml"

# How far back to fetch from RSS
DEFAULT_LOOKBACK_WEEKS = 2

# CSV columns (explicit ordering - matches legacy format)
CSV_COLUMNS = [
    "entry_title",
    "entry_url",
    "rss_url",
    "entry_date",
    "text",
    "tags",
    "report_id",
    "author_email",
]


@contextmanager
def _insecure_ssl_context():
    """
    Temporarily disable SSL verification for feeds with expired/self-signed certs.
    
    Restores original context on exit to avoid affecting other code.
    """
    original_context = getattr(ssl, '_create_default_https_context', None)
    try:
        if hasattr(ssl, "_create_unverified_context"):
            ssl._create_default_https_context = ssl._create_unverified_context
        yield
    finally:
        if original_context is not None:
            ssl._create_default_https_context = original_context
        elif hasattr(ssl, '_create_default_https_context'):
            delattr(ssl, '_create_default_https_context')


def _is_recent(entry_published: str, lookback: timedelta) -> bool:
    """
    Check if an entry was published within the lookback window.
    
    Args:
        entry_published: Date string like "Wed, 29 Jan 2025 14:30:00 +0000"
        lookback: Maximum age for an entry to be considered recent
        
    Returns:
        True if entry is within the lookback window
    """
    date_fmt = "%a, %d %b %Y %H:%M:%S %z"
    try:
        entry_dt = datetime.strptime(entry_published, date_fmt)
        now_utc = datetime.now(timezone.utc)
        return now_utc - entry_dt <= lookback
    except ValueError:
        logger.warning(f"Could not parse date: {entry_published}")
        return False


def _parse_rss_entry(entry, feed_url: str) -> dict | None:
    """
    Parse a single RSS entry into structured data.
    
    Args:
        entry: A feedparser entry object
        feed_url: The source feed URL (for metadata)
        
    Returns:
        Dict with entry data, or None on failure
    """
    import re
    
    try:
        soup = bs4.BeautifulSoup(entry.summary, "html.parser")
        paragraphs = soup.find_all("p")
        
        # Extract author and report ID from expected structure
        author = ""
        report_id = ""
        
        if paragraphs:
            author = re.sub(r"^Author:\s*", "", paragraphs[0].get_text(strip=True))
        if len(paragraphs) > 1:
            report_id = re.sub(r"^Report ID:\s*", "", paragraphs[1].get_text(strip=True))
        
        if not report_id:
            logger.warning(f"No report ID found for entry: {entry.title}")
            return None
        
        # Clean body text
        text = soup.get_text(separator=" ")
        text = re.sub(r"[\n\t]", " ", text)
        text = re.sub(r"[,;]", "", text)
        text = re.sub(r"^.*Report ID:\s*\d+\s*", "", text)
        text = re.sub(r"\s*Images attached to this report\s*", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        
        # Extract first tag if present (serialize as string for CSV)
        tags = ""
        if hasattr(entry, 'tags') and entry.tags:
            tags = str(entry.tags[0])
        
        return {
            "report_id": report_id,
            "entry_title": entry.title,
            "entry_url": entry.link,
            "rss_url": feed_url,
            "entry_date": entry.published,
            "text": text,
            "tags": tags,
            "author_email": author,
        }
    
    except Exception as e:
        title = getattr(entry, 'title', 'unknown')
        logger.warning(f"Failed to parse entry '{title}': {e}")
        return None


def _fetch_and_save_raw_feed(lab: str, feed_url: str, data_path: Path) -> bytes | None:
    """
    Fetch raw XML from RSS feed and save for debugging.
    
    Args:
        lab: Lab identifier (LHO or LLO)
        feed_url: URL to fetch
        data_path: Directory to save raw file
        
    Returns:
        Raw XML bytes, or None if fetch failed
    """
    try:
        # Create unverified context for LIGO's problematic certs
        context = ssl._create_unverified_context() if hasattr(ssl, "_create_unverified_context") else None
        
        request = urllib.request.Request(feed_url)
        response = urllib.request.urlopen(request, context=context, timeout=30)
        raw_xml = response.read()
        
        # Save raw for debugging
        raw_filename = ALOG_RAW_FILENAME_TEMPLATE.format(lab=lab)
        raw_path = data_path / raw_filename
        raw_path.write_bytes(raw_xml)
        logger.info(f"Saved raw feed: {raw_filename} ({len(raw_xml):,} bytes)")
        
        return raw_xml
        
    except Exception as e:
        logger.error(f"Failed to fetch {lab} feed: {e}")
        return None


def _parse_feed_entries(raw_xml: bytes, feed_url: str, lookback: timedelta) -> list[dict]:
    """
    Parse raw XML into list of entry dicts.
    
    Args:
        raw_xml: Raw XML bytes from feed
        feed_url: Original feed URL (for metadata)
        lookback: Maximum age for entries
        
    Returns:
        List of parsed entry dicts
    """
    feed = feedparser.parse(raw_xml)
    
    if feed.bozo:
        logger.warning(f"Feed parse warning: {feed.bozo_exception}")
    
    entries = []
    failed_count = 0
    
    for entry in feed.entries:
        if not _is_recent(entry.published, lookback):
            continue
        
        parsed = _parse_rss_entry(entry, feed_url)
        if parsed:
            entries.append(parsed)
        else:
            failed_count += 1
    
    if failed_count > 0:
        logger.warning(f"Failed to parse {failed_count} entries")
    
    return entries


def _fetch_recent_entries(data_path: Path, weeks: int = DEFAULT_LOOKBACK_WEEKS) -> list[dict]:
    """
    Fetch recent entries from all RSS feeds, saving raw XML for each.
    
    Args:
        data_path: Directory to save raw files
        weeks: How many weeks back to include
        
    Returns:
        List of parsed entry dicts
    """
    lookback = timedelta(weeks=weeks)
    all_entries = []
    
    for lab, feed_url in LIGO_RSS_URLS.items():
        logger.info(f"Fetching {lab} aLOG feed...")
        
        raw_xml = _fetch_and_save_raw_feed(lab, feed_url, data_path)
        if raw_xml is None:
            continue
        
        lab_entries = _parse_feed_entries(raw_xml, feed_url, lookback)
        logger.info(f"Fetched {len(lab_entries)} entries from {lab}")
        all_entries.extend(lab_entries)
    
    return all_entries


def fetch_alog_entries(data_folder_path: Path | str | None = None) -> Path | None:
    """
    Fetch aLOG entries and merge with existing historical data.
    
    Maintains a single deduplicated CSV that grows over time, suitable for
    both summarization (filter to recent) and future RAG ingestion (full history).
    
    Raw XML files are saved for debugging (overwritten each run).
    
    Args:
        data_folder_path: Directory for output. Defaults to config.DATA_FOLDER_PATH.
        
    Returns:
        Path to the CSV file, or None if fetch failed.
    """
    data_path = Path(data_folder_path) if data_folder_path else config.DATA_FOLDER_PATH
    csv_path = data_path / ALOG_EXPORT_FILENAME
    
    # Fetch new entries from RSS (also saves raw XML)
    new_entries = _fetch_recent_entries(data_path)
    
    if not new_entries:
        logger.warning("No new entries fetched from RSS feeds")
        if csv_path.exists():
            logger.info(f"Using existing data: {csv_path}")
            return csv_path
        return None
    
    new_df = pd.DataFrame(new_entries, columns=CSV_COLUMNS)
    
    # Merge with existing data if present
    if csv_path.exists():
        try:
            existing_df = pd.read_csv(csv_path, dtype=str)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            logger.info(f"Merged {len(new_df)} new entries with {len(existing_df)} existing")
        except Exception as e:
            logger.warning(f"Could not read existing CSV, starting fresh: {e}")
            combined_df = new_df
    else:
        combined_df = new_df
    
    # Deduplicate by report_id (keep most recent)
    before_dedup = len(combined_df)
    combined_df = combined_df.drop_duplicates(subset=["report_id"], keep="last")
    combined_df = combined_df.reset_index(drop=True)
    
    if before_dedup != len(combined_df):
        logger.info(f"Deduplicated: {before_dedup} -> {len(combined_df)} entries")
    
    # Write back (overwrite with clean, deduplicated data)
    combined_df.to_csv(csv_path, index=False)
    logger.info(f"aLOG data saved: {csv_path} ({len(combined_df)} total entries)")
    
    return csv_path


# Legacy alias for compatibility
def main(data_folder_path: str) -> Path | None:
    """Legacy entry point. Use fetch_alog_entries() instead."""
    return fetch_alog_entries(data_folder_path)


if __name__ == "__main__":
    result = fetch_alog_entries()
    if result:
        logger.info(f"Success: {result}")
    else:
        logger.error("Failed to fetch aLOG entries")