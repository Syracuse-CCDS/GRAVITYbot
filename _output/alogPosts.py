#####################################################################################################
# DOCUMENTATION NOTES : #############################################################################
# File Creator: Alexander O. Smith (2025-present), aosmith@syr.edu
# Current Maintainer: Alexander O. Smith, aosmith@syr.edu
# Last Update: April 2, 2025
# Program Goal:
# This file posts the aLOG summary "GRAVITYbot"
#####################################################################################################
#####################################################################################################
# DEPENDENCIES ######################################################################################
# Package Dependencies
import os, sys, requests, markdown, markdownify
from dotenv import find_dotenv, load_dotenv
from panoptes_client.panoptes import Talk, Panoptes
#####################################################################################################
# Getting dotenv credentials necessary to send the message.
_ = load_dotenv(find_dotenv())
username = os.environ.get("PANOPTES_USER")
password = os.environ.get("PANOPTES_PASS")
user_id = os.environ.get("PANOPTES_ID") #os.environ.get("PANOPTES_USER")
#####################################################################################################
def alog_board_post(current_day, username=username, password=password):

    Panoptes.connect(username=username, password=password)

    # Build the message 
    talk = Talk()
    # This needs to be generated and updated to whatever the discussion ID is, 
    # It is at the end of the URL of the discussion post
    board_id = 6945

    # Formatting message to post
    # This needs to be updated so that it finds the current file
    #f = open('_output/LLOaLogForumSummary_2025-04-01.md', 'r')
    #html_gpt = markdown.markdown( f.read() )
    #markdown_string = markdownify.markdownify(html_gpt)

    # Read the Markdown file
    labs = ['LLO', 'LHO']
    for l in labs:
        try:
            with open(f'_output/{l}aLogForumSummary_{current_day}.md', 'r', encoding='utf-8') as file:
                alog_sum = file.readlines()
            
            discussion_title = f'{l} aLOG Summary: {current_day}\n'

            # Modify the content as needed
            # For example, add a new header

            alog_sum.insert(0, f'## {l} aLOG Summary: {current_day}\n')

            alog_sum = ''.join(alog_sum)

            # Final message
            body = alog_sum

            # Sending the message body to the discussion_id location
            payload = {"discussions": {
                "title":discussion_title, "board_id":board_id, "comments":[{"body":body}]
                }}

            # Posting the message
            talk.http_post('discussions', json=payload)
        
        except:
            print(f'There is no {l} aLOG file affiliated with {current_day}.')


#####################################################################################################
# From Laura and Cliff:
#
# from panoptes_client.panoptes import Talk
# talk = Talk()
# user_id = USER_ID_TO_POST_COMMENT
# discussion_id = ID_OF_DISCUSSION_THREAD
# body = POST CONTENT
# payload = { 'comments': {
#                        'user_id': user_id, 'discussion_id': discussion_id, 'body': body
#                }}
# 
# talk.http_post('comments', json=payload)
# 
# Notice your user_id =/= your username. 
# You can map a login to a user_id using the User.where() function:
# from panoptes_client import User
# user = next(User.where(login='your-user-name'))
# print(user.id)
#
# You need to login so that the Client can pass along the appropriate API token as part of the request. Following the Client documentation (see https://panoptes-python-client.readthedocs.io/en/latest/user_guide.html#usage-examples), add the following login command at the beginning of the script:
#
# Note: to keep credentials out of script and logs, you could use the following alternatives:
#a) Panoptes.connect(login='interactive') # command will prompt for username and/or password
#b) Set PANOPTES_USERNAME and PANOPTES_PASSWORD environment variables that would be accessible via os.environ.get() call.