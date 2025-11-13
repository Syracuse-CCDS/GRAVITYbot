import json
import os
import io
import tarfile

import dotenv
import panoptes_client

_ = dotenv.load_dotenv(dotenv.find_dotenv())
username = os.environ.get("PANOPTES_USER")
password = os.environ.get("PANOPTES_PASS")

client = panoptes_client.Panoptes.connect(username=username , password=password)
project = panoptes_client.Project(1104)

print("====================")

try:
    project.generate_export("talk_comments")
except panoptes_client.panoptes.PanoptesAPIException as e:
    print("Todays talk export likely esists")
    print(e)

response = project.get_export("talk_comments", generate=False)
export_bytes = io.BytesIO(response.content)
with tarfile.open(fileobj=export_bytes, mode='r:*') as tar:
    first_memeber = tar.getmembers()[0]

    first_memeber_name = first_memeber.name
    first_memeber_rename = first_memeber_name.replace(".json", ".csv")
    extracted_bytes = tar.extractfile(first_memeber)
    extracted_text = extracted_bytes.read().decode('utf-8')  # or decode appropriately

print(first_memeber_name, first_memeber_rename)
extracted_data = json.loads(extracted_text)

#for row in content:
#    print(row["comment_created_at"])
