import json
import requests
from pathlib import Path

#---INSERT CODE TO COLLECT ITEM IDS HERE----

# Or use this test set of ids that have small files (To use, delete the '#' in the next line)
item_ids = [12706085]
#item_ids = [17714843,153788] #test items
folder_path = "data/raw/"


#Set the base URL
BASE_URL = 'https://api.figshare.com/v2'
api_call_headers = {'Authorization': 'token $env:FIGSHARE_TOKEN'}

file_info = [] #a blank list to hold all the file metadata

print('Retrieving metadata')
for i in item_ids:
    r = requests.get(BASE_URL + '/articles/' + str(i) + '/files')
    file_metadata = json.loads(r.text)
    for j in file_metadata: #add the item id to each file record- this is used later to name a folder to save the file to
        j['item_id'] = i
        file_info.append(j) #Add the file metadata to the list
print('Files available' + str(file_info))

#Download each file to a subfolder named for the article id and save with the file name
for k in file_info:
    print('Downloading '+k['name'])
    response = requests.get(BASE_URL + '/file/download/' + str(k['id']), headers=api_call_headers)
    dir_path = Path(folder_path) / str(k['item_id'])
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / k['name']
    file_path.write_bytes(response.content)
    print(k['name']+ ' downloaded')
    
print('All files have been downloaded in '+ str(folder_path))