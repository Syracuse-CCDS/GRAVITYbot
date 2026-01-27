"""
GRAVITYbot - Main Entry Point
-----------------------------
Runs both Talk and aLOG summary pipelines.

For independent runs, use:
  - __talk_summary_main__.py (Talk summaries + email)
  - __alog_summary_main__.py (aLOG summaries + Zooniverse posts)
"""
import datetime
import os
import sys

# Add paths for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../_data')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../_output')))

import config

if config.DRY_RUN:
    print("=" * 50)
    print("DRY RUN MODE - No emails or posts will be sent")
    print("=" * 50)

import __talk_summary_main__ as talk_summary
import __alog_summary_main__ as alog_summary


def main():
    """Run both Talk and aLOG summary pipelines."""
    print("=" * 50)
    print("GRAVITYbot - Running all summaries")
    print("=" * 50)
    
    print("\n[1/2] Running Talk summary...")
    talk_summary.main()
    
    print("\n[2/2] Running aLOG summary...")
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    alog_summary.main(utc_now)
    
    print("\n" + "=" * 50)
    print("GRAVITYbot - Complete")
    print("=" * 50)


if __name__ == "__main__":
    main()