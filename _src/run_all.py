"""
GRAVITYbot - Main Entry Point
-----------------------------
Runs both Talk and aLOG summary pipelines.

For independent runs, use:
  - talk_summary.py (Talk summaries + email)
  - alog_summary.py (aLOG summaries + Zooniverse posts)
"""
import datetime
import logging
import os
import sys

# Add project root to path for config import
# TODO: Remove when proper packaging is implemented
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config

# Import the summary modules (will be renamed from __dunder__ versions)
import talk_summary
import alog_summary

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    """Run both Talk and aLOG summary pipelines."""
    logger.info("=" * 50)
    logger.info("GRAVITYbot - Running all summaries")
    if config.DRY_RUN:
        logger.info("DRY RUN MODE - No emails or posts will be sent")
    logger.info("=" * 50)
    
    logger.info("\n[1/2] Running Talk summary...")
    talk_summary.main()
    
    logger.info("\n[2/2] Running aLOG summary...")
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    alog_summary.main(utc_now)
    
    logger.info("\n" + "=" * 50)
    logger.info("GRAVITYbot - Complete")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()