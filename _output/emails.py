#####################################################################################################
# DOCUMENTATION NOTES : #############################################################################
# File Creator: Alexander O. Smith (2024-present), aosmith@syr.edu
# Current Maintainer: Alexander O. Smith, aosmith@syr.edu
# Last Update: April 02, 2025
# Program Goal:
# This file sends emails and automates posts to forums that are returned from GRAVITYbot summaries.
#####################################################################################################
# NOTICE: 
# 1. For this functionality to work, you need to get an Google App password and add all the proper
# GOOGLE_APP_XXX variables in the dotenv file.
# 2. You will need to make sure that the "recipients" email(s) will accept email from the "sender."
#####################################################################################################
# DEPENDENCIES ######################################################################################
# Package Dependencies
from dotenv import find_dotenv, load_dotenv     # Loading env file
import os, smtplib, ssl                         # OS and server/mail protocol libraries
from email.mime.text import MIMEText            # Email Formatting

def talk_email(date, body):
    # Email Subject/Body "Hello There" Email Test
    subject = "GRAVITYbot Talk Summary: " + date
    md_body = body
    
    # TO-DO: Format email here

    return subject, md_body

# A function that sends email
def send_email(subject, body):
    # Loading the necessary info for the email from env file
    _ = load_dotenv(find_dotenv())
    SMTP_PORT = 587
    SMTP_HOST = os.environ.get("SMTP_HOST")
    SMTP_USER = os.environ.get("SMTP_USER")
    SMTP_PASSWORD =  os.environ.get("SMTP_PASS")
    MSG_FROM = os.environ.get("SMTP_FROM")
    MSG_TO = os.environ.get("SMTP_TO")
    # Makeing Message Variables
    MSG_BODY = body
    MSG_SUBJECT = subject

    msg = MIMEText(MSG_BODY,  'plain')
    msg['Subject'] = MSG_SUBJECT
    msg['From'] = MSG_FROM
    msg['To'] = MSG_TO
    
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASSWORD)
    server.sendmail(MSG_FROM, [MSG_TO], msg.as_string())
    server.quit()


def main(date, body):
    email = talk_email(date, body)
    send = send_email(email[0], email[1])

# To Do: #############################################################################################
