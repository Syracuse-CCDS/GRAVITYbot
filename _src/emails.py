"""
emails.py

Handles email sending for GRAVITYbot summaries.

Requirements:
    - SMTP credentials configured in .env (SMTP_HOST, SMTP_USER, SMTP_PASS, SMTP_FROM, SMTP_TO)

Original Author: Alexander O. Smith <aosmith@syr.edu>
"""
import logging
import os
import smtplib
import sys
from email.message import EmailMessage

import markdown

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
SMTP_PORT = 587


def format_summary_email(date_str: str, summary_content: str, summary_type: str = "talk") -> tuple[str, str, str]:
    """
    Format a summary for email delivery.
    
    Args:
        date_str: Date string (YYYY-MM-DD) for the subject line
        summary_content: The raw markdown summary text
        summary_type: Type of summary ("talk" or "alog") for subject line
        
    Returns:
        tuple: (subject, html_content, plain_text_content)
    """
    if summary_type == "talk":
        subject = f"GRAVITYbot Talk Summary: {date_str}"
    else:
        subject = f"GRAVITYbot aLOG Summary: {date_str}"
    
    # Remove Zooniverse-specific link formatting for email
    plain_text = summary_content.replace("+tab+", "")
    
    # Convert markdown to HTML
    html = markdown.markdown(
        plain_text,
        extensions=['fenced_code', 'codehilite', 'extra', 'sane_lists', 'nl2br']
    )
    
    return subject, html, plain_text


def send_email(subject: str, html: str, text: str) -> None:
    """
    Send an email via SMTP with HTML and plain text versions.
    
    Args:
        subject: Email subject line
        html: HTML formatted email body
        text: Plain text fallback body
        
    Raises:
        smtplib.SMTPException: If email sending fails
    """
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = config.SMTP_FROM
    msg['To'] = config.SMTP_TO
    msg.set_content(text)
    msg.add_alternative(html, subtype='html')

    with smtplib.SMTP(config.SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASS)
        server.sendmail(config.SMTP_FROM, [config.SMTP_TO], msg.as_string())
    
    logger.info(f"Email sent to {config.SMTP_TO}")


def send_talk_summary_email(date_str: str, summary_content: str) -> None:
    """
    Send a Talk summary email.
    
    Args:
        date_str: Date string (YYYY-MM-DD) for the subject
        summary_content: The markdown summary to send
    """
    subject, html, text = format_summary_email(date_str, summary_content, "talk")
    send_email(subject, html, text)


def send_alog_summary_email(date_str: str, summary_content: str, lab: str) -> None:
    """
    Send an aLOG summary email.
    
    Args:
        date_str: Date string (YYYY-MM-DD) for the subject
        summary_content: The markdown summary to send
        lab: Lab identifier ("LHO" or "LLO") for the subject line
    """
    subject = f"GRAVITYbot {lab} aLOG Summary: {date_str}"
    
    plain_text = summary_content.replace("+tab+", "")
    html = markdown.markdown(
        plain_text,
        extensions=['fenced_code', 'codehilite', 'extra', 'sane_lists', 'nl2br']
    )
    
    send_email(subject, html, plain_text)