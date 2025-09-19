import os
import pandas as pd
from datetime import datetime, timezone

print(os.getcwd())

date = datetime.now(timezone.utc).strftime('%Y-%m-%d')

talkJson = pd.read_json(f'./_data/project-1104-comments_{date}.json')
talkJson.to_csv(f'./_data/project-1104-comments_{date}.csv')
talkDB = pd.read_csv(f'./_data/project-1104-comments_{date}.csv')

boards = [6872, 6945, 6946] # This will reduce the risk of circular summaries
talk_data = talkDB[talkDB.board_id.isin(boards)]

print('Dropping Irrelevant User Ids...')
drop_ids = [2630456, 2877652]
talk_data = talk_data[talk_data.comment_user_id.isin(drop_ids) == False]

print('Writing CSV...')
output_datafile = 'GRAVITYbot_talk_discussion.csv'
write_header = not os.path.exists(output_datafile)
talk_data.to_csv('./_data/'+output_datafile, mode='a', header=write_header, index=False)

existing = pd.read_csv('./_data/'+output_datafile).drop_duplicates()
existing.to_csv('./test/'+output_datafile, index=False)
