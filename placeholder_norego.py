import sys
import requests
import pandas as pd

site = "https://australs2020.herokuapp.com"
slug = "australs2020"
api_key = "API Key"
category_url = "https://australs2020.herokuapp.com/api/v1/tournaments/australs2020/speaker-categories/1"

# Get a list of speakers from Tabbycat, and compare who has not registered
request = requests.get('{}/api/v1/tournaments/{}/speakers'.format(site, slug), headers = {'Authorization':'Token {}'.format(api_key)})
response = request.json()

# Get a list of people who have registered
reg_csv = pd.read_csv('2020 Monash Australs Individual Registration (Responses) - Form Responses 1.csv')

names = list(reg_csv['What is your preferred first and last name?'])

for speaker in response:
    spk = speaker
    if speaker['name'].startswith("Placeholder"):
        spk['categories'].append(category_url)

        post_request = requests.post('{}/api/v1/tournaments/{}/speakers/{}'.format(site, slug, speaker['id']), json=spk, headers = {'Authorization':'Token {}'.format(api_key)})
        assert post_request.status_code == 200, post_request.status_code
        print("Speaker {} updated (No Rego).".format(speaker['name']))
