"""App helper functions
"""
import requests
import random
import pandas as pd

EVENT_URL = 'https://site.web.api.espn.com/apis/site/v2/sports/golf/leaderboard?league=pga'

PGA_URL = "https://www.pgatour.com/stats/stat.109.html"
NON_PGA_URL = "https://www.pgatour.com/stats/stat.02677.html"

def get_event_info():
    try:
        r = requests.get(EVENT_URL)
        data = r.json()

        # Get the current event name
        event_name = data['events'][0]['name']
        # Get the players in the field, who have yet to tee off
        avail_picks = [a['athlete']['displayName'] for a in data['events'][0]['competitions'][0]['competitors'] if a['status']['type']['state'] == 'pre']

        tournament_state = data['events'][0]['status']['type']
    except Exception as e:
        print("Issue getting data from ESPN API. Message: {}".format(e))

    return event_name, avail_picks, tournament_state

def get_picks():
    avail_picks = ["TW", "PM", "DJ", "AS"]
    return avail_picks


def get_event():
    return "Test Open"


def get_earnings(player):

    # Column configuration
    player_col = "PLAYER NAME"
    pga_earnings_col = "MONEY"
    non_earnings_col = "TOTAL MONEY"

    # Loop through PGA and Non-PGA tour Money lists.
    for M_URL in [PGA_URL, NON_PGA_URL]:
        html = requests.get(M_URL).content
        df_list = pd.read_html(html)

        # Extract the player DF
        player_df = df_list[-1]

        # Make all text lower string for matching
        player_df[player_col] = player_df[player_col].str.lower()

        # Make the players a list
        registered_players = list(player_df[player_col])

        if player.lower() in registered_players:
            try:
                earnings = list(player_df[player_df[player_col] == player.lower()][pga_earnings_col])[0]
            except Exeption as e:
                earnings = list(player_df[player_df[player_col] == player.lower()][non_earnings_col])[0]
            
            # Extract the value
            if isinstance(earnings, str):
                return int(earnings.replace('$', '').replace(',', ''))
            elif isinstance(earnings, float) or isinstance(earnings, int):
                return int(earnings)

    # TODO: send an e-mail to administrator saying user needs to be added manually.   
    return 0.

def construct_user_table(users, picks):
    user_dict = {
        'Name': [],
        'Total Earnings': [],
        'Strikes Remaining': [],
    }

    for usr in users:
        user_dict['Name'].append(usr.name)
        user_dict['Strikes Remaining'].append(int(usr.strikes_remaining))
        user_dict['Total Earnings'].append(sum([int(x.points) for x in picks if x.name == usr.name]))

    user_df = pd.DataFrame(user_dict)

    user_df.sort_values(['Total Earnings'], inplace=True, ascending=False)
    user_df["Rank"] = user_df['Total Earnings'].rank(ascending=False).astype(int)

    max_points = user_df['Total Earnings'].max()
    user_df["Delta"] = [x - max_points for x in user_df['Total Earnings']]
    
    # Reorder columns
    user_df = user_df[['Rank', 'Name', 'Total Earnings', 'Delta', 'Strikes Remaining']]

    return user_df.to_html(classes='data', border=0, index=False)