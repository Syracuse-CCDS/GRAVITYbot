"""
emails.py

Original Author:
    Alexander O. Smith <aosmith@syr.edu>

Purpose:
    Handles email sending for GRAVITYbot Talk summaries.

Requirements:
    - SMTP credentials configured in .env (SMTP_HOST, SMTP_USER, SMTP_PASS, SMTP_FROM, SMTP_TO)
"""

import os
import smtplib
import sys
from email.message import EmailMessage

import markdown

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


def send_talk_summary_email(date):
    """
    Sends the Talk summary email.

    Args:
        date (str): Date string (YYYY-MM-DD) for the summary.
    """
    subject, html, text = format_talk_email(date)
    send_email(subject, html, text)


if __name__ == "__main__":
    import datetime
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    print(f"Testing email for date: {today}")
    send_talk_summary_email(today)