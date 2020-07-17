import sys
import pandas as pd
import requests

api_key = "API Key"
venue_csv = pd.read_csv('2020 Monash Australs Individual Registration (Responses) - Sheet10.csv')

response = requests.get('https://australs2020.herokuapp.com/api/v1/tournaments/australs2020/venue-categories', headers = {'Authorization':'Token {}'.format(api_key)})
raise Exception(response.json())

for index,row in venue_csv.iterrows():
    name = str(row['name'])
    cat_id = name.split(".")[0]

    j = {
        'name': name,
        'priority': 100,
        'categories': ['https://australs2020.herokuapp.com/api/v1/tournaments/australs2020/venue-categories/{}'.format(cat_id)]
    }

    response = requests.post('https://australs2020.herokuapp.com/api/v1/tournaments/australs2020/venues', json=j, headers = {'Authorization':'Token {}'.format(api_key)})
    assert response.status_code == 200, response.status_code
