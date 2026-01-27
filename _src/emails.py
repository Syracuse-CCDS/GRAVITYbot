"""
emails.py

Original Author:
    Alexander O. Smith <aosmith@syr.edu>

Purpose:
    Handles email sending and Talk forum posting for GRAVITYbot summaries.

Requirements:
    - SMTP credentials configured in .env (SMTP_HOST, SMTP_USER, SMTP_PASS, SMTP_FROM, SMTP_TO)
    - Panoptes credentials for Talk posting (PANOPTES_USER, PANOPTES_PASS)
    - Recipient email must accept messages from the sender address
"""

import os
import smtplib
import sys
from email.message import EmailMessage

import markdown
import panoptes_client

# Add project root to path for config import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config


def format_talk_email(date):
    """
    Reads the Talk summary markdown file and formats it for email.

    Args:
        date (str): Date string (YYYY-MM-DD) for the summary file.

    Returns:
        tuple: (subject, html_content, plain_text_content)
    """
    subject = f"GRAVITYbot Talk Summary: {date}"
    
    summary_path = config.OUTPUT_FOLDER_PATH / f"ZooniverseTalkSummary_{date}.md"
    
    with open(summary_path, "r", encoding="utf-8") as md_file:
        text = md_file.read().replace("+tab+", "")
        html = markdown.markdown(
            text, 
            extensions=['fenced_code', 'codehilite', 'extra', 'sane_lists', 'nl2br']
        )

    return subject, html, text


def send_email(subject, html, text):
    """
    Sends an email via SMTP with HTML and plain text versions.

    Args:
        subject (str): Email subject line.
        html (str): HTML formatted email body.
        text (str): Plain text fallback body.
    """
    smtp_port = 587

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = config.SMTP_FROM
    msg['To'] = config.SMTP_TO
    msg.set_content(text)
    msg.add_alternative(html, subtype='html')

    server = smtplib.SMTP(config.SMTP_HOST, smtp_port)
    server.starttls()
    server.login(config.SMTP_USER, config.SMTP_PASS)
    server.sendmail(config.SMTP_FROM, [config.SMTP_TO], msg.as_string())
    server.quit()
    
    print(f"Email sent to {config.SMTP_TO}")


def post_talk_to_zooniverse(current_day):
    """
    Posts the Talk summary to the Zooniverse Talk forum.

    Args:
        current_day (str): Date string (YYYY-MM-DD) for the summary.
    """
    board_id = 6946  # Gravity Spy Talk board

    panoptes_client.Panoptes.connect(
        username=config.PANOPTES_USER,
        password=config.PANOPTES_PASS
    )

    summary_path = config.OUTPUT_FOLDER_PATH / f"ZooniverseTalkSummary_{current_day}.md"
    
    with open(summary_path, 'r', encoding='utf-8') as file:
        talk_sum = file.read()

    discussion_title = f"Gravity Spy Talk Summary: {current_day}"
    
    discussion_footer = """
NOTICE: Summary created by GRAVITYbot, an LLM powered summarizer maintained by Gravity Spy researchers
and is under construction and is subject to updates in training. Full documentation and development can
be found at the [Syracuse CCDS GitHub](https://github.com/Syracuse-CCDS/GRAVITYbot). Any concerns,
questions, or recommended updates can be directed to the Syracuse Gravity Spy research team.
    """.strip().replace("\n", " ")

    body = f"## Talk Summary: {current_day}\n\n{talk_sum}\n\n{discussion_footer}"

    payload = {
        "discussions": {
            "title": discussion_title,
            "board_id": board_id,
            "comments": [{"body": body}]
        }
    }

    talk = panoptes_client.panoptes.Talk()
    talk.http_post('discussions', json=payload)
    
    print(f"Talk summary posted to Zooniverse board {board_id}")


def main(date, body=None):
    """
    Main entry point: sends email and posts to Zooniverse Talk.

    Args:
        date (str): Date string (YYYY-MM-DD) for the summary.
        body (str, optional): Unused, kept for backward compatibility.
    """
    # Send email
    subject, html, text = format_talk_email(date)
    send_email(subject, html, text)
    
    # Post to Zooniverse Talk forum
    if config.DRY_RUN:
        print("DRY RUN: Skipping Zooniverse Talk post")
    else:
        post_talk_to_zooniverse(date)


if __name__ == "__main__":
    import datetime
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    print(f"Testing email/post for date: {today}")
    main(today)