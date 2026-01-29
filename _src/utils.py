"""
utils.py

Shared utilities for GRAVITYbot.
"""

import re


def clean_text(text, source=None):
    """
    Cleans and normalizes comment text by removing URLs, mentions, greetings,
    unwanted punctuation, and extra whitespace.

    Args:
        text (str): The raw comment text to clean.
        source (str, optional): Source type for additional cleaning rules.
            - "talk": Applies Zooniverse Talk-specific patterns
            - "alog": Applies aLOG-specific patterns (default behavior)
            - None: Base cleaning only

    Returns:
        str: The cleaned and normalized text.
    """
    if not text:
        return ""
    
    # Talk-specific: remove deleted comment placeholders
    if source == "talk":
        text = re.sub(r"This comment has been deleted", "", text)

    # Common: remove URLs
    text = re.sub(r"https?://\S+", " ", text)
    
    # Common: remove @mentions
    text = re.sub(r"@\w+", " ", text)
    
    # Common: remove greetings
    text = re.sub(r"Hi,\n|Hello,\n", "", text, flags=re.IGNORECASE)
    
    # Common: remove thanks
    text = re.sub(r"Thanks|Thank you", "", text, flags=re.IGNORECASE)
    
    # Common: remove special characters (keep alphanumeric, basic punctuation)
    text = re.sub(r"[^A-Za-z0-9>\s'\"?.!]", " ", text)
    
    # Common: collapse repeated periods
    text = re.sub(r"\.+", " ", text)
    
    # Talk-specific: remove Zooniverse boilerplate
    if source == "talk":
        text = re.sub(r"projects zooniverse gravity spy talk subjects", " ", text)
        text = re.sub(r"zooniverse gravity spy talk comment page", " ", text)
    
    # Common: remove standalone single letters (b-z)
    text = re.sub(r"\s[b-z][.\s]", " ", text)
    
    # Common: remove standalone 'v'
    text = re.sub(r"^v$", "", text)
    
    # Common: replace newlines with spaces
    text = re.sub(r"[\n\t]", " ", text)
    
    # Talk-specific: remove number patterns common in Talk data
    if source == "talk":
        text = re.sub(r"[0-9]+\s", " ", text)
        text = re.sub(r"[a-z][0-9]+", " ", text)
    
    # aLOG-specific: remove attached image references
    if source == "alog":
        text = re.sub(r"Images attached to this report", " ", text)
    
    # Common: collapse whitespace
    text = re.sub(r"\s+", " ", text)
    
    return text.strip()


def clean_talk_text(text):
    """Convenience wrapper for Talk comment cleaning."""
    return clean_text(text, source="talk")


def clean_alog_text(text):
    """Convenience wrapper for aLOG comment cleaning."""
    return clean_text(text, source="alog")