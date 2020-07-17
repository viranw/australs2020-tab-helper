
import requests
import pandas as pd

site = "https://australs2020.herokuapp.com"
slug = "australs2020"
api_key = "API Key"

esl = 'https://australs2020.herokuapp.com/api/v1/tournaments/australs2020/speaker-categories/2'
efl = 'https://australs2020.herokuapp.com/api/v1/tournaments/australs2020/speaker-categories/3'


# Load in CSV

# Get a list of speakers and their URLs from Tabbycat

# For each speaker in the CSV:
# - If they don't exist in Tabbycat, flag this
# - If they do, run a get request to get their JSON, modify to add categories, and then post it back
speaker_names = []
speaker_ids = {}
request = requests.get('{}/api/v1/tournaments/{}/speakers'.format(site, slug), headers = {'Authorization':'Token {}'.format(api_key)})
response = request.json()

for speaker in response:
    speaker_ids[speaker['name']] = speaker['id']
    speaker_names.append(speaker['name'])

status_csv = pd.read_csv('status.csv')

#raise Exception(status_csv)

for index, row in status_csv.iterrows():
    speaker = row['name']
    status = row['status']
    if speaker not in speaker_names:
        print("{} doesn't exist in Tabbycat.".format(speaker))
        continue

    id = speaker_ids[speaker]

    if status == "ESL" or status == "EFL":
        speaker_json = get = requests.get('{}/api/v1/tournaments/{}/speakers/{}'.format(site, slug, id), headers = {'Authorization':'Token {}'.format(api_key)}).json()
        if status == "EFL":
            speaker_json['categories'] = [esl, efl]
        elif status == "ESL":
            speaker_json['categories'] = [esl]

        request = requests.post('{}/api/v1/tournaments/{}/speakers/{}'.format(site, slug, id), json=speaker_json, headers = {'Authorization':'Token {}'.format(api_key)})
        assert request.status_code == 200, "Error when uploading {}".format(speaker)
        print("Updated {}".format(speaker))

print("Updated {} speakers.".format(len(status_csv)))
