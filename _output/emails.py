#####################################################################################################
# DOCUMENTATION NOTES : #############################################################################
# File Creator: Alexander O. Smith (2024-present), aosmith@syr.edu
# Current Maintainer: Alexander O. Smith, aosmith@syr.edu
# Last Update: May 22, 2025
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
from panoptes_client.panoptes import Talk, Panoptes
import os, smtplib, ssl                         # OS and server/mail protocol libraries
from email.mime.text import MIMEText            # Email Formatting
# Getting dotenv credentials necessary to send the message.

_ = load_dotenv(find_dotenv())
username = os.environ.get("PANOPTES_USER")
password = os.environ.get("PANOPTES_PASS")
user_id = os.environ.get("PANOPTES_ID") #os.environ.get("PANOPTES_USER")

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
    # Making Message Variables
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

def talk_board_post(current_day, username=username, password=password):

    Panoptes.connect(username=username, password=password)

    # Build the message 
    talk = Talk()
    # This needs to be generated and updated to whatever the discussion ID is, 
    # It is at the end of the URL of the discussion post
    board_id = 6946


    # Read the Markdown file
    with open(f'_output/ZooniverseTalkSummary_{current_day}.md', 'r', encoding='utf-8') as file:
        talk_sum = file.readlines()
    
    discussion_title = f'Gravity Spy Talk Summary: {current_day}\n'

    # Modify the content as needed
    # For example, add a new header

    talk_sum.insert(0, f'## Talk Summary: {current_day}\n')

    talk_sum = ''.join(talk_sum) +'\n\n NOTICE: Summary created by GRAVITYbot, an LLM powered summarizer maintained by Gravity Spy researchers. Full documentation and development can be found at the [Syracuse CCDS GitHub](https://github.com/Syracuse-CCDS/GRAVITYbot). Any concerns, questions, or recommended updates can be directed to the Syracuse Gravity Spy research team.'

    # Final message
    body = talk_sum

    # Sending the message body to the discussion_id location
    payload = {"discussions": {
        "title":discussion_title, "board_id":board_id, "comments":[{"body":body}]
        }}

    # Posting the message
    talk.http_post('discussions', json=payload)



def main(date, body):
    email = talk_email(date, body)
    #send = send_email(email[0], email[1])
    talk_post = talk_board_post(date)

# To Do: #############################################################################################
