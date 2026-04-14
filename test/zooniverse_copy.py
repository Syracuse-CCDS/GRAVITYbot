"""
zooniverse.py

Single interface for all Zooniverse/Panoptes interactions:
- Fetching Talk export data (for summarization and RAG ingestion)
- Posting summaries to Talk forums

Raw JSON exports are retained for debugging (overwritten each run).
Each Zooniverse export is treated as the complete source of truth.
"""

import io
import logging
import os
import re
import shutil
import sys
import tarfile
import urllib.request
from pathlib import Path

import panoptes_client

# Add project root to path for config import
# TODO: Remove when proper packaging is implemented
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import utils_copy as utils

import config

logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------
# Constants
# ---------------------

# Gravity Spy project ID on Zooniverse
PROJECT_ID = 1104

# Output filenames
TALK_EXPORT_FILENAME = "talk_posts.csv"
TALK_RAW_FILENAME = "talk_posts_raw.json"

# Board IDs for posting different summary types
SUMMARY_BOARD_IDS = {
    "talk": 6946,  # Gravity Spy Talk summaries
    "alog": 6945,  # aLOG summaries (LHO/LLO)
}

# Footer appended to all posted summaries
DISCUSSION_FOOTER = (
    "NOTICE: Summary created by GRAVITYbot, an LLM powered summarizer maintained "
    "by Gravity Spy researchers and is under construction and is subject to updates "
    "in training. Full documentation and development can be found at the "
    "[Syracuse CCDS GitHub](https://github.com/Syracuse-CCDS/GRAVITYbot). "
    "Any concerns, questions, or recommended updates can be directed to the "
    "Syracuse Gravity Spy research team."
)

# Phrases that indicate the LLM produced a fallback/empty summary
INVALID_SUMMARY_INDICATORS = [
    "cannot provide the structured outline",
    "no data from",
    "i cannot provide",
    "if you have data or further instructions",
]


# ---------------------
# Authentication
# ---------------------

_authenticated = False


def _authenticate() -> None:
    """
    Authenticate with the Panoptes (Zooniverse) API.

    Uses credentials from config.PANOPTES_USER and config.PANOPTES_PASS.

    This is idempotent — calling multiple times is safe and will only
    authenticate once per session. The panoptes_client library caches
    credentials internally after the first successful authentication.

    Raises:
        panoptes_client.panoptes.PanoptesAPIException: If authentication fails
    """
    global _authenticated

    if _authenticated:
        return

    panoptes_client.Panoptes.connect(
        username=config.PANOPTES_USER, password=config.PANOPTES_PASS
    )
    _authenticated = True
    logger.debug("Authenticated with Panoptes API")


# ---------------------
# Fetching Talk Data
# ---------------------


def fetch_talk_export(data_folder_path: Path | str | None = None) -> Path | None:
    """
    Download and extract Talk comment data from Zooniverse.

    This is the primary data source for both:
    - GRAVITYbot summarization
    - RAG chatbot ingestion

    Raw JSON is retained for debugging (overwritten each run).
    Each export is treated as the complete source of truth.

    Args:
        data_folder_path: Directory to store the exported data.
            Defaults to config.DATA_FOLDER_PATH.

    Returns:
        Path to the exported CSV file, or None if export failed.

    Notes:
        - Requires valid PANOPTES_USER and PANOPTES_PASS in config
        - Panoptes limits export generation to once per 24 hours
    """
    data_path = Path(data_folder_path) if data_folder_path else config.DATA_FOLDER_PATH
    csv_path = data_path / TALK_EXPORT_FILENAME

    # Step 1: Authenticate with Panoptes
    try:
        _authenticate()
    except panoptes_client.panoptes.PanoptesAPIException as e:
        logger.error(f"Panoptes authentication failed: {e}")
        logger.info("Will attempt to use existing data if available")
        return _find_existing_export(csv_path)

    # Step 2: Request Talk export
    export_url = _request_talk_export()
    if export_url is None:
        logger.warning(
            "Could not get Talk export URL, using existing data if available"
        )
        return _find_existing_export(csv_path)

    # Step 3: Download and extract raw JSON
    raw_json_path = _download_and_extract_raw(export_url, data_path)
    if raw_json_path is None:
        return _find_existing_export(csv_path)

    # Step 4: Convert to CSV
    csv_path = _convert_to_csv(raw_json_path, csv_path)
    return csv_path


def prepare_local_export(
    json_path: Path | str, data_folder_path: Path | str | None = None
) -> Path | None:
    """
    Convert a local raw JSON export to the canonical CSV.

    Use for dry runs or when fetch_talk_export() cannot download fresh data
    but a raw JSON file is available locally (e.g., manually downloaded or
    from a prior extraction that was never converted).

    Args:
        json_path: Path to a project-{id}-comments_*.json file
        data_folder_path: Directory for output. Defaults to config.DATA_FOLDER_PATH.

    Returns:
        Path to the CSV file, or None if conversion failed.
    """
    json_path = Path(json_path)
    if not json_path.exists():
        logger.error(f"JSON file not found: {json_path}")
        return None

    data_path = Path(data_folder_path) if data_folder_path else config.DATA_FOLDER_PATH
    csv_path = data_path / TALK_EXPORT_FILENAME

    # Copy to canonical raw filename
    raw_json_path = data_path / TALK_RAW_FILENAME
    if json_path.resolve() != raw_json_path.resolve():
        shutil.copy2(json_path, raw_json_path)
        logger.info(f"Copied {json_path.name} -> {TALK_RAW_FILENAME}")

    csv_path = _convert_to_csv(raw_json_path, csv_path)

    if csv_path is not None:
        # Clean up dated JSON files now that canonical CSV exists
        for json_file in data_path.glob(f"project-{PROJECT_ID}-comments_*.json"):
            json_file.unlink()
            logger.debug(f"Removed dated file: {json_file.name}")

    return csv_path


def find_best_local_export(data_folder_path: Path | str | None = None) -> Path | None:
    """
    Find the best available local export data without contacting Zooniverse.

    Prefers unconverted JSON (e.g., a manually downloaded or previously
    extracted dated file) over an existing canonical CSV, since the JSON
    may be newer.

    Use for dry runs or when the Zooniverse download is unavailable.

    Args:
        data_folder_path: Directory to search. Defaults to config.DATA_FOLDER_PATH.

    Returns:
        Path to a CSV file (converting JSON if needed), or None if no usable data found.
    """
    data_path = Path(data_folder_path) if data_folder_path else config.DATA_FOLDER_PATH
    csv_path = data_path / TALK_EXPORT_FILENAME
    return _find_existing_export(csv_path)


def _request_talk_export() -> str | None:
    """
    Request a Talk export URL from Panoptes API.

    Returns:
        URL string for downloading the export, or None if request failed.
    """
    project = panoptes_client.Project(PROJECT_ID)

    # Try to get existing or generate new export
    try:
        project.get_export(export_type="talk_comments", generate=True, wait=False)
        export_info = project.describe_export("talk_comments")
        url = export_info["data_requests"][0]["url"]
        logger.info(f"Talk export URL obtained: {url[:80]}...")
        return url

    except panoptes_client.panoptes.PanoptesAPIException as e:
        logger.warning(f"Export request failed (may be rate limited): {e}")

        # Retry with generate-then-get pattern
        try:
            project.generate_export("talk_comments")
            project.get_export(export_type="talk_comments")
            export_info = project.describe_export("talk_comments")
            url = export_info["data_requests"][0]["url"]
            logger.info(f"Talk export URL obtained (retry): {url[:80]}...")
            return url
        except Exception as retry_error:
            logger.error(f"Export retry also failed: {retry_error}")
            return None

    except Exception as e:
        logger.error(f"Unexpected error requesting export: {e}")
        return None


def _download_and_extract_raw(url: str, data_path: Path) -> Path | None:
    """
    Download tarball from URL and extract raw JSON.

    Inspects tarball members directly to identify the comment file,
    avoiding confusion with stale files from prior runs in data_path.

    Args:
        url: URL to the Talk export tarball
        data_path: Directory to extract files into

    Returns:
        Path to the raw JSON file, or None if extraction failed.
    """
    try:
        logger.info("Downloading Talk export...")
        response = urllib.request.urlopen(url)
        tarball_bytes = response.read()

        logger.info("Extracting tarball...")
        file_obj = io.BytesIO(tarball_bytes)
        with tarfile.open(fileobj=file_obj, mode="r:gz") as tar:
            # Identify comment file(s) from tarball members before extracting
            comment_members = [
                m
                for m in tar.getmembers()
                if re.match(rf"project-{PROJECT_ID}-comments_.*\.json$", m.name)
            ]

            if not comment_members:
                logger.error("No comment JSON files found in tarball")
                return None

            if len(comment_members) > 1:
                logger.warning(
                    f"Multiple comment files in tarball: "
                    f"{[m.name for m in comment_members]}"
                )
                comment_members.sort(key=lambda m: m.name, reverse=True)

            logger.info(f"Tarball contains: {[m.name for m in comment_members]}")
            tar.extractall(path=str(data_path))

        source_json = data_path / comment_members[0].name

        # Rename to canonical raw filename (overwrites previous)
        raw_json_path = data_path / TALK_RAW_FILENAME
        source_json.replace(raw_json_path)
        logger.info(f"Saved raw export: {TALK_RAW_FILENAME}")

        # Clean up any dated JSON files (from this or prior extractions)
        for json_file in data_path.glob(f"project-{PROJECT_ID}-comments_*.json"):
            json_file.unlink()
            logger.debug(f"Removed dated file: {json_file.name}")

        return raw_json_path

    except Exception as e:
        logger.error(f"Failed to download/extract Talk data: {e}")
        return None


def _convert_to_csv(raw_json_path: Path, csv_path: Path) -> Path | None:
    """
    Convert raw JSON export to CSV.

    Each Zooniverse export is the complete source of truth,
    so this simply overwrites any existing CSV.

    Args:
        raw_json_path: Path to the raw JSON file
        csv_path: Path to the canonical CSV file

    Returns:
        Path to the CSV file, or None if conversion failed.
    """
    try:
        utils.convert_json_to_csv(raw_json_path, csv_path)
        logger.info(f"Talk data saved: {csv_path}")

        # Dated CSVs should not exist; warn if they do and clean up
        for old_csv in csv_path.parent.glob(f"project-{PROJECT_ID}-comments_*.csv"):
            logger.warning(f"Removing unexpected legacy CSV: {old_csv.name}")
            old_csv.unlink()

        return csv_path

    except Exception as e:
        logger.error(f"Failed to convert Talk data: {e}")
        return None


def _find_existing_export(csv_path: Path) -> Path | None:
    """
    Find existing usable export data.

    Used as fallback when fresh export cannot be obtained.
    Prefers unconverted JSON over stale CSV, since a dated JSON
    file may be newer than the last successfully converted CSV.

    Returns:
        Path to CSV file, or None if no usable data found.
    """
    data_path = csv_path.parent

    # First: check for a raw JSON that hasn't been converted yet
    json_files = sorted(
        data_path.glob(f"project-{PROJECT_ID}-comments_*.json"),
        key=lambda p: p.name,
        reverse=True,
    )
    if json_files:
        logger.info(f"Found unconverted JSON export: {json_files[0].name}")
        return prepare_local_export(json_files[0], data_path)

    # Second: check for canonical CSV from a prior successful run
    if csv_path.exists():
        logger.info(f"Using existing Talk export: {csv_path.name}")
        return csv_path

    # Dated CSVs should not exist; flag if they do
    stale_csvs = list(data_path.glob(f"project-{PROJECT_ID}-comments_*.csv"))
    if stale_csvs:
        logger.warning(
            f"Found unexpected legacy CSV files (cleanup issue?): "
            f"{[f.name for f in stale_csvs]}"
        )

    logger.error(f"No existing Talk export found in {data_path}")
    return None


# ---------------------
# Summary Validation
# ---------------------


def _is_valid_summary(content: str) -> bool:
    """
    Check that summary content is substantive, not an LLM fallback.

    Returns False if content is empty, too short, or contains known
    phrases that indicate the LLM had no data to summarize.
    """
    stripped = content.strip()
    if not stripped or len(stripped) < 150:
        return False
    content_lower = stripped.lower()
    return not any(ind in content_lower for ind in INVALID_SUMMARY_INDICATORS)


# ---------------------
# Posting Summaries
# ---------------------


def post_summary(
    summary_type: str,
    date_str: str,
    summary_content: str,
    title: str | None = None,
    lab: str | None = None,
) -> None:
    """
    Post a summary to the appropriate Zooniverse Talk forum.

    Validates that summary_content is substantive before posting.
    If the content appears to be an LLM fallback (no data available),
    the post is skipped and a warning is logged.

    Args:
        summary_type: Type of summary - "talk" or "alog"
        date_str: Date string (YYYY-MM-DD) for the summary
        summary_content: The summary text to post
        title: Custom discussion title. Auto-generated if not provided.
        lab: Lab identifier ("LHO" or "LLO") - required for alog summaries

    Raises:
        ValueError: If summary_type is invalid or lab is missing for alog
    """
    if summary_type not in SUMMARY_BOARD_IDS:
        raise ValueError(f"Unknown summary type: {summary_type}. Use 'talk' or 'alog'.")

    if summary_type == "alog" and not lab:
        raise ValueError("Lab identifier required for alog summaries")

    board_id = SUMMARY_BOARD_IDS[summary_type]

    # Generate default title
    if title is None:
        if summary_type == "talk":
            title = f"Gravity Spy Talk Summary: {date_str}"
        else:
            title = f"{lab} aLOG Summary: {date_str}"

    # Validate summary content before posting
    if not _is_valid_summary(summary_content):
        logger.warning(
            f"Skipping post for '{title}': "
            "summary content is empty or appears to be an LLM fallback"
        )
        return

    # Build discussion body with footer
    body = f"## {title}\n\n{summary_content}\n\n{DISCUSSION_FOOTER}"

    # Zooniverse convention: +tab+ prefix opens links in new tab
    body = re.sub(r"\]\(https://", r"](+tab+https://", body)

    # Build and send payload
    payload = {
        "discussions": {
            "board_id": board_id,
            "title": title,
            "comments": [{"body": body}],
        }
    }

    _authenticate()

    talk = panoptes_client.panoptes.Talk()
    talk.http_post("discussions", json=payload)

    logger.info(f"Posted '{title}' to Zooniverse board {board_id}")


def post_talk_summary(date_str: str, summary_content: str) -> None:
    """Post a Talk summary to Zooniverse."""
    post_summary("talk", date_str, summary_content)


def post_alog_summary(date_str: str, summary_content: str, lab: str) -> None:
    """Post an aLOG summary to Zooniverse."""
    post_summary("alog", date_str, summary_content, lab=lab)
