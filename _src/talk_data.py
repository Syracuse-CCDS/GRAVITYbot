"""
talk_data.py

Original Author:
    Alexander O. Smith <aosmith@syr.edu>

Purpose:
    This script accesses "Talk" comments through the Zooniverse API (Panoptes).
    It downloads, extracts, and converts Talk comment exports for downstream
    summarization by GRAVITYbot.

References:
    - Zooniverse API Authentication: https://zooniverse.github.io/panoptes/#authentication
    - Panoptes Python Client: https://github.com/zooniverse/panoptes-python-client
    - Panoptes CLI: https://github.com/zooniverse/panoptes-cli
    - Contact: contact@zooniverse.org

Known Limitations:
    - Panoptes limits export generation to once per 24 hours per project
    - Export generation can fail intermittently; script falls back to older data
"""

import datetime
import io
import os
import sys
import tarfile
import urllib.request

import pandas
import panoptes_client

# Add project root to path for config import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config


def get_talk_data(slug, data_folder_path):
    """
    Downloads and extracts Talk comment data from Zooniverse for the given project.

    Args:
        slug (str): The Zooniverse project slug (e.g., "zooniverse/gravity-spy").
        data_folder_path (str): Path to folder where Talk data should be stored.

    Returns:
        str: The URL of the downloaded Talk export, or None if download failed.

    Notes:
        - Requires valid PANOPTES_USER and PANOPTES_PASS in environment/config.
        - Panoptes limits export generation to once per 24 hours.
        - Extracts tarball and converts JSON to CSV for downstream processing.
    """
    # Connect to Panoptes
    panoptes_client.Panoptes.connect(
        username=config.PANOPTES_USER,
        password=config.PANOPTES_PASS
    )

    # Get project ID from slug
    project = panoptes_client.Project.find(slug=str(slug))
    proj_id = int(str(project).split(' ')[1].split('>')[0])

    # Attempt to get/generate Talk export
    talk_url = None
    try:
        panoptes_client.Project(proj_id).get_export(
            export_type='talk_comments', 
            generate=True, 
            wait=False
        )
        talk_describe = panoptes_client.Project(proj_id).describe_export('talk_comments')
        talk_url = talk_describe['data_requests'][0]['url']
        print(f"Talk export URL: {talk_url}")

    except Exception:
        # Retry with different approach
        try:
            panoptes_client.Project(proj_id).generate_export('talk_comments')
            panoptes_client.Project(proj_id).get_export(export_type='talk_comments')
            talk_describe = panoptes_client.Project(proj_id).describe_export('talk_comments')
            talk_url = talk_describe['data_requests'][0]['url']
            print(f"Talk export URL (retry): {talk_url}")
        except Exception as e:
            print(f"Failed to get Talk export: {e}")

    if talk_url is None:
        print(f"""
WARNING: Talk description URL is empty.
    Panoptes API did not generate a download URL.
    This may be a Panoptes bug or rate limit.
    Continuing with existing data if available...
        """)
        return None

    # Download and extract tarball
    try:
        talk_response = urllib.request.urlopen(talk_url).read()
        file_obj = io.BytesIO(talk_response)
        
        with tarfile.open(fileobj=file_obj, mode='r:gz') as tar:
            tar.extractall(path=data_folder_path)

        # Convert JSON to CSV
        current_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        json_path = f"{data_folder_path}/project-1104-comments_{current_date}.json"
        csv_path = f"{data_folder_path}/project-1104-comments_{current_date}.csv"

        try:
            talk_df = pandas.read_json(json_path)
            talk_df.to_csv(csv_path, index=False)
            print(f"Talk data saved: {csv_path}")
        except FileNotFoundError:
            print(f"Note: Export file not dated today ({current_date}), using existing data.")

    except Exception as e:
        print(f"Failed to download/extract Talk data: {e}")
        return None

    return talk_url


def main(data_folder_path=None):
    """
    Main entry point for Talk data retrieval.

    Args:
        data_folder_path (str, optional): Path to data folder. 
            Defaults to config.DATA_FOLDER_PATH.

    Returns:
        str: The Talk export URL if successful, None otherwise.
    """
    if data_folder_path is None:
        data_folder_path = str(config.DATA_FOLDER_PATH)

    slug = config.PANOPTES_SLUG

    try:
        return get_talk_data(slug, data_folder_path)

    except panoptes_client.panoptes.PanoptesAPIException as error:
        print(f"""
!!! PANOPTES API EXCEPTION !!!
Raw Exception Output: "{error}"
    Perhaps you have called talk data more than once in the last 24 hours.
    NOTICE: Panoptes API warnings are not particularly well documented.
    See PANOPTES documentation:
    - https://panoptes-python-client.readthedocs.io/en/latest/panoptes_client.html#panoptes_client.panoptes
    It is not uncommon for data retrieval to fail. Perhaps try again later? 
    Stopping talk_data.py...
    Attempting summary on older data...
        """)
        return None


if __name__ == "__main__":
    result = main()
    if result:
        print(f"Talk data retrieval complete: {result}")
    else:
        print("Talk data retrieval failed or using cached data.")