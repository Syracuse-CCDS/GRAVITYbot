#####################################################################################################
# DOCUMENTATION NOTES : #############################################################################
# File Creator:         Alexander O. Smith, aosmith@syr.edu
# Current Maintainer:   Alexander O. Smith, aosmith@syr.edu
# Past Maintainers:     Alexander O. Smith (6/05/2024-present)
# Last Update:          April 01, 2025
# Program Goal:
# This file is designed to access "Talk" comments from through the Zooniverse API, Panoptes
#####################################################################################################
# IMPORTANT REFERENCES/GUIDES: ######################################################################
# Zooniverse/Panoptes API Guides:
# Zooniverse API Authentication Info:       https://zooniverse.github.io/panoptes/#authentication
# Zooniverse Panoptes Python Client Info:   https://github.com/zooniverse/panoptes-python-client
# Zooniverse Panoptes Command Client Info:  https://github.com/zooniverse/panoptes-cli
# Zooniverse/Panoptes Contact Info:
# Contact for API Questions: contact@zooniverse.org
#   Notice, Laura Trouille claims emails to this contact cannot handle major debugging until at least
#   September of 2024. However, the contact email will reach her and the whole team for responses.
#####################################################################################################
#####################################################################################################
# DEPENDENCIES ######################################################################################
import os, requests, json, tarfile, dotenv
from io import BytesIO
from panoptes_client import panoptes, Panoptes, Project, exportable
from dotenv import find_dotenv, load_dotenv
from datetime import date, datetime
import urllib.request as urllib2
import pandas as pd
#####################################################################################################

def get_talk_dat(slug):
    ### VALIDATING CREDENTIALS FOR DOWNLOADING TALK DATA ###
    # Make sure your Panoptes log-in credentials are added to the .env file
    _ = load_dotenv(find_dotenv())
    p_user = os.environ.get("PANOPTES_USER")
    p_pass = os.environ.get("PANOPTES_PASS")
    client = Panoptes.connect(username = p_user , password = p_pass)

    # Get Project ID via the project slug: make sure slug is in .env file
    project = Project.find(slug=str(slug))
    proj_id = int(str(project).split(' ')[1].split('>')[0])

    ### RETRIEVES TALK DATA FROM ZOONIVERSE VIA PANOPTES API ###
    # Getting the EXPORT URL: generates talk export and retrieves it
    try:
        #talk_gen = Project(proj_id).generate_export('talk_comments')
        #talk_export = Project(proj_id).get_export(export_type='talk_comments', generate=True, wait=False)
        talk_gen = Project(proj_id).get_export(export_type='talk_comments', generate=True, wait=False)
        talk_describe = Project(proj_id).describe_export('talk_comments')
        talk_url = talk_describe['data_requests'][0]['url']
        print(f'Expected Data URL, talk_url: {talk_url}')

    except:
        talk_gen = Project(proj_id).generate_export('talk_comments')
        talk_export = Project(proj_id).get_export(export_type='talk_comments')#, generate=True)
        talk_describe = Project(proj_id).describe_export('talk_comments')
        #print(talk_describe)
        talk_url = talk_describe['data_requests'][0]['url']
        print(f'Talk_url: {talk_url}')

    # Tarfile URL location in talk_describe dictionary object
    #talk_url = talk_describe['data_requests'][0]['url']
    if talk_url == None:
        return print(
            f"""
!!! WARNING: Talk description URL is empty !!!\n Talk URL = {talk_url}
    Panoptes' API's "get_export" did not generate a URL to download the data.
    This is a possible bug with Panoptes' API.
    Continuing with the talk summary using non-current data...
            """)
    # Localizing the tarfile and extracting it to ./_data directory
    else:
        talk_req = urllib2.urlopen(talk_url).read()
        file = BytesIO(talk_req)
        with tarfile.open(fileobj=file, mode='r:gz') as tar:
            # Extracting talk data
            tar.extractall(path="./_data")
        current_date = datetime.utcnow()
        date = current_date.strftime('%Y-%m-%d')
        try:
            talk_dat = pd.read_json(f'./_data/project-1104-comments_{date}.json')
            talk_dat.to_csv(f'./_data/project-1104-comments_{date}.csv')
        except:
            print(f'File {str(file)} is not from the current date, {date}.')

    return talk_url


def main():
    _ = load_dotenv(find_dotenv())
    slug = os.environ.get("PANOPTES_SLUG")
    try:
        talk_dat = get_talk_dat(slug)
    except panoptes.PanoptesAPIException as error:
        exception = SystemExit(error)
        warning = f"""
!!! PANOPTES API EXCEPTION !!!
Raw Exception Output: "{exception}"\n
    Perhaps you have called talk data more than once in the last 24 hours.\n
    NOTICE: Panoptes API warnings are not particularly well documented.
    See PANOPTES documentation:
    - https://panoptes-python-client.readthedocs.io/en/latest/panoptes_client.html#panoptes_client.panoptes\n
    It is not uncommon for data retrieval to fail. Perhaps try again later? \n
    Stopping talk_data.py...\n
    Attempting summary on older data...
        """

        return print(warning)

    # Clean up and format talk data

talk = main()
#####################################################################################################
# To Do/Possible Improvements:
# 1. Make more dynamic to deal with Panoptes API issues and once-per-day downloads
# 2. Figure out how to delete/backup older data
# 3. Clean up output from this file. It's messy, and not all of it is helpful.
#####################################################################################################
