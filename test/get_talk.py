"""
GRAVITYbot - Talk Data Script
--------------------------------
Fetches Zooniverse Talk forum data for local testing.

Author: Alexander O. Smith (2024-present)
Maintainer: Alexander O. Smith <aosmith@syr.edu>
"""

import logging
import os
import sys

import pandas as pd

# Add project root to path for config import
# TODO: Remove when proper packaging is implemented
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import utils_copy as utils
import zooniverse_copy as zooniverse

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def load_talk_data(file_path):
    """
    Load and preprocess Talk forum data.

    Args:
        file_path: Path to the Talk export CSV

    Returns:
        DataFrame with timestamp, comment, and comment_url columns
    """
    talk_url = "https://www.zooniverse.org/projects/zooniverse/gravity-spy/talk/"

    df = pd.read_csv(file_path, encoding="utf8")

    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                df["comment_created_at"], utc=True, format="mixed"
            ),
            "comment": df["comment_body"].fillna("").apply(utils.clean_talk_text),
            "comment_url": df.apply(
                lambda row: f"{talk_url}{row['board_id']}/{row['discussion_id']}",
                axis=1,
            ),
        }
    )


def main():
    """Run the get_talk pipeline."""
    logger.info("------------------")
    logger.info("Starting Download...")
    if config.DRY_RUN:
        logger.info("GETTING RAW TALK DOWNLOAD")
    logger.info("------------------")

    # Fetch data (or use best available in dry run mode)
    config.DRY_RUN:
    csv_path = zooniverse.find_best_local_export()
    if csv_path is None:
        logger.error("DRY RUN: No existing data (CSV or JSON) available")
        return
    logger.info(f"DRY RUN: Using data from {csv_path}")


if __name__ == "__main__":
    main()
