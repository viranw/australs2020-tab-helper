import sys
import requests
import pandas as pd
from gsheets import Sheets

assert len(sys.argv) == 2, "Usage: python ballot_check.py <round seq>"

round_seq = sys.argv[1]

# Collect URLs for teams and adjudicators - Tabbycat API references these URLs inside Debate objects
site = "https://australs2020.herokuapp.com"
slug = "australs2020"
api_key = "API Key"

teams = {}
teams_by_id = {}
request = requests.get('{}/api/v1/tournaments/{}/teams'.format(site, slug), headers = {'Authorization':'Token {}'.format(api_key)})
response = request.json()

for team in response:
    short = team['short_name']
    url = team['url']

    teams[short] = team
    teams_by_id[url] = team


adjudicators = {}
chairs = []
adjs_by_id = {}
request = requests.get('{}/api/v1/tournaments/{}/adjudicators'.format(site, slug), headers = {'Authorization':'Token {}'.format(api_key)})
response = request.json()

for adj in response:
    name = adj['name']
    url = adj['url']

    adjudicators[name] = adj
    adjs_by_id[url] = adj

venues = {}
request = requests.get('{}/api/v1/tournaments/{}/venues'.format(site, slug), headers = {'Authorization':'Token {}'.format(api_key)})
response = request.json()

for venue in response:
    venues[venue['url']] = venue['name']


# Download debate data and clean it
debates = []
request = requests.get('{}/api/v1/tournaments/{}/rounds/{}/pairings'.format(site, slug, round_seq), headers = {'Authorization':'Token {}'.format(api_key)})
response = request.json()

for raw_debate in response:
    debate = raw_debate
    id = debate['id']

    # Convert chair/panellists from URLs to names
    adjs = []
    adjs.append(adjs_by_id[debate['adjudicators']['chair']]['name'])
    chairs.append(adjs_by_id[debate['adjudicators']['chair']]['name'])

    for panellist in debate['adjudicators']['panellists']:
        adjs.append(adjs_by_id[panellist]['name'])

    # No trainees (obvs)
    debate['adjudicators'] = adjs
    debate['venue'] = venues[debate['venue']]

    debates.append(debate)

# Get the debate_teams CSV
debateteams_csv = pd.read_csv("debateteams.csv", index_col="id")
all_aff_debateteams = debateteams_csv.loc[debateteams_csv['side']=="aff"]
all_neg_debateteams = debateteams_csv.loc[debateteams_csv['side']=="neg"]

# Get the scores CSV
scores_csv = pd.read_csv("scores.csv", index_col="id")
scores_csv['score'] = scores_csv['score'].round(2)

# Get the CSV - Name of judge and scores
sheets = Sheets.from_files('~/client_secrets.json', '~/storage.json')
url = 'https://docs.google.com/spreadsheets/d/1B-iczHBRNnVA1nZgPgkVkWFU0jF3veDBsWAxlrmmUHg'
s = sheets.get(url)
csv = s.find('Form responses 1').to_csv('google_ballot.csv', encoding='utf-8', dialect='excel')
google_csv = pd.read_csv('google_ballot.csv', index_col="Full Name")

debates = sorted(debates, key=lambda obj: obj['venue'], reverse=False)

debates_ok = 0
for debate in debates:
    aff_totals = [0,0,0,0]
    neg_totals = [0,0,0,0]
    counted_ballots = 0

    aff_win = 0
    neg_win = 0

    proceed = True

    for adj in debate['adjudicators']:
        try:
            sub = google_csv.loc[adj]
        except Exception:
            print("No submission from {} yet - Can't mark Debate {}.".format(adj, debate['venue']))
            print("---")
            proceed = False
            break

        # Check if in minority or not
        aff_t = 0
        neg_t = 0
        #print(sub)
        for s in sub.iteritems():
            if s[0].endswith("Affirmative") or s[0].startswith("Affirmative"):
                #print(s)
                aff_t += float(s[1])
            elif s[0].endswith("Negative") or s[0].startswith("Negative"):
                neg_t += float(s[1])
        """
        if aff_t == neg_t:
            raise Exception("{} has a tied Google ballot".format(adj))
        elif aff_t > neg_t:
            aff_win += 1
        elif aff_t < neg_t:
            neg_win += 1

        """
        try:
            if aff_t == neg_t:
                raise Exception("{} has a tied Google ballot".format(adj))
            elif aff_t > neg_t:
                aff_win += 1
            elif aff_t < neg_t:
                neg_win += 1
        except Exception:
            print("Multiple Googles from {}".format(adj))


    if not proceed:
        continue

    # Determine who the winner is
    if aff_win == neg_win:
        winner = "split"
    elif aff_win > neg_win:
        winner = "aff"
    elif aff_win < neg_win:
        winner = "neg"

    #print("{} {}".format(aff_win, neg_win))

    # Only count ballots if they're in the majority
    for adj in debate['adjudicators']:
        sub = google_csv.loc[adj]

        # Check if in minority or not
        aff_t = 0
        neg_t = 0
        for s in sub.iteritems():
            if s[0].endswith("Affirmative") or s[0].startswith("Affirmative"):
                aff_t += float(s[1])
            if s[0].endswith("Negative") or s[0].startswith("Negative"):
                neg_t += float(s[1])

        if winner == "split" and adj not in chairs:
            #print("{} in minority".format(adj))
            continue
        elif winner == "aff" and aff_t < neg_t:
            #rint("{} in minority".format(adj))
            continue
        elif winner == "neg" and aff_t > neg_t:
            #rint("{} in minority".format(adj))
            continue
        else:
            counted_ballots += 1
            aff_totals[0] += float(sub['1st Affirmative'])
            aff_totals[1] += float(sub['2nd Affirmative'])
            aff_totals[2] += float(sub['3rd Affirmative'])
            aff_totals[3] += float(sub['Affirmative Reply'])

            neg_totals[0] += float(sub['1st Negative'])
            neg_totals[1] += float(sub['2nd Negative'])
            neg_totals[2] += float(sub['3rd Negative'])
            neg_totals[3] += float(sub['Negative Reply'])


    # Get averages for the positions in the debate
    aff_averages = [0,0,0,0]
    neg_averages = [0,0,0,0]
    #print(aff_totals)
    #print(neg_totals)
    for i in range(0, len(aff_totals)):
        score = aff_totals[i]
        aff_averages[i] = score / counted_ballots

    for i in range(0, len(neg_totals)):
        score = neg_totals[i]
        neg_averages[i] = score / counted_ballots


    # Get the AFF and NEG debate_team IDs from the TC CSV
    aff_debateteam = all_aff_debateteams.loc[all_aff_debateteams['debate_id']==debate['id']]
    neg_debateteam = all_neg_debateteams.loc[all_neg_debateteams['debate_id']==debate['id']]

    assert len(aff_debateteam) == 1, "More than one AFF debate team returned for the debate!"
    assert len(neg_debateteam) == 1, "More than one NEG debate team returned for the debate!"

    aff_dt_id = aff_debateteam.index.values.astype(int)[0]
    neg_dt_id = neg_debateteam.index.values.astype(int)[0]

    # Get scores from the scores_csv
    aff_scores = scores_csv.loc[scores_csv['debate_team_id']==aff_dt_id]
    neg_scores = scores_csv.loc[scores_csv['debate_team_id']==neg_dt_id]

    assert len(aff_scores) == 4, len(aff_scores)
    assert len(neg_scores) == 4, len(neg_scores)

    ok = True
    incomp = True

    # AFF
    for i in range(0,4):
        tc_score_block = aff_scores.loc[aff_scores['position']==i+1]['score'].values.astype(float)
        if len(tc_score_block) == 0:
            print("No TC scores for {}".format(debate['venue']))
            tc_score = -1
            incomp = True
        else:
            tc_score = tc_score_block[0]

        google_score = float(aff_averages[i])

        aff_scores.loc[aff_scores['position']==i+1, 'google_score'] = google_score

    # NEG
    for i in range(0,4):
        tc_score_block = neg_scores.loc[neg_scores['position']==i+1]['score'].values.astype(float)
        if len(tc_score_block) == 0:
            print("No TC scores for {}".format(debate['venue']))
            tc_score = -1
            incomp = True
        else:
            tc_score = tc_score_block[0]
        google_score = float(neg_averages[i])

        neg_scores.loc[neg_scores['position']==i+1, 'google_score'] = google_score

    ok = True
    errors = []
    for index, row in aff_scores.iterrows():
        if abs(row['score'] - row['google_score']) > 0.01:
            errors.append("{} vs {} for AFF Pos {}".format(row['score'], row['google_score'], row['position']))
            ok = False

    for index, row in neg_scores.iterrows():
        if abs(row['score'] - row['google_score']) > 0.01:
            errors.append("{} vs {} for NEG Pos {}".format(row['score'], row['google_score'], row['position']))
            ok = False

    if len(errors) > 0:
        print("Discrepancies in Room {}:".format(debate['venue']))
        for error in errors:
            print(error)
    else:
        debates_ok += 1
        print("Debate {} OK.".format(debate['venue']))
    print("---")
print("{} debates checked, {} OK".format(len(debates), debates_ok))
