"""
zotero_get.py

Original Author:
    Alexander O. Smith <aosmith@syr.edu>

Purpose:
    Fetches Zotero PDFs and metadata from the LLM_RAG_papers collection in the
    GravitySpy_SU group Zotero folder and puts them in the proper local diretory.

    - zot_get(): Uses the Zotero API to fetch PDFs and metadata for a given paper.
    - zot_save(): Saves the fetched PDF and metadata to the local directory.
"""

import os

import zotero
from dotenv import load_dotenv

load_dotenv()

# zotero API credentials
zot_api_key = os.getenv("ZOT_API_KEY")
zot_group_id = os.getenv("ZOT_GROUP_ID")

# zot: establishes the connection to the zotero API using the pyzotero api wrapper
zot = zotero.Zotero(
    # library id: connects to the zotero_group_id defined in the API section
    library_id=zot_group_id,
    # library_type: the zot_group_id is of the "group" class
    library_type="group",
    # api_key: the zotero API key defined in the API section
    api_key=zot_api_key,
)


def zot_get(zot):
    # items: fetches all items in the LLM_RAG_papers collection
    items = zot.everything(zot.collection_items("RMXHTMEV"))

    pdf_dir = "../pdfs"
    os.makedirs(pdf_dir, exist_ok=True)

    for item in items:
        # Get all PDF attachments (including children)
        if (
            item["data"].get("itemType") == "attachment"
            and item["data"].get("contentType") == "application/pdf"
        ):
            # Direct PDF attachment
            pdf_items = [item]
        else:
            # Get children that are PDFs
            pdf_items = [
                child
                for child in zot.children(item["key"])
                if child["data"].get("contentType") == "application/pdf"
            ]

        # Download each PDF
        for pdf in pdf_items:
            filename = pdf["data"].get("filename", f"{pdf['key']}.pdf")
            filepath = os.path.join(pdf_dir, filename)
            zot.dump(pdf["key"], filepath)
            print(f"Downloaded: {filename}")

    return


"""
Backlog:
    - Make zot_get()
    - Make zot_save()
    -
"""
