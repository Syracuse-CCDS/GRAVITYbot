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


SMTP_PORT = 587


def _markdown_to_html(content: str) -> str:
    """Convert markdown content to HTML."""
    return markdown.markdown(
        content,
        extensions=['fenced_code', 'codehilite', 'extra', 'sane_lists', 'nl2br']
    )


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
    subject = f"GRAVITYbot Talk Summary: {date_str}"
    send_email(subject, _markdown_to_html(summary_content), summary_content)


def send_alog_summary_email(date_str: str, summary_content: str, lab: str) -> None:
    """
    Send an aLOG summary email.
    
    Args:
        date_str: Date string (YYYY-MM-DD) for the subject
        summary_content: The markdown summary to send
        lab: Lab identifier ("LHO" or "LLO") for the subject line
    """
    subject = f"GRAVITYbot {lab} aLOG Summary: {date_str}"
    send_email(subject, _markdown_to_html(summary_content), summary_content)