"""App helper functions
"""
import os
import random
import smtplib
import ssl
import subprocess
from email.mime.text import MIMEText

import pandas as pd
import requests

"""
https://pthree.org/2012/01/07/encrypted-mutt-imap-smtp-passwords/
https://gist.github.com/bnagy/8914f712f689cc01c267
"""

EVENT_URL = (
    "https://site.web.api.espn.com/apis/site/v2/sports/golf/leaderboard?league=pga"
)

PGA_URL = "https://www.pgatour.com/stats/stat.109.html"
NON_PGA_URL = "https://www.pgatour.com/stats/stat.02677.html"


def send_email(receiver_email, subject, html):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    # sender_email = os.environ.get("USER_EMAIL")
    # password = os.environ.get("USER_PW")
    sender_email = "1993oad@gmail.com"
    password = os.getenv("OADPW")

    # print (password)
    message = "{}".format(html)
    msg = MIMEText(message, "html")
    msg["Subject"] = subject
    msg["From"] = sender_email

    context = ssl.create_default_context()
    server = smtplib.SMTP_SSL(smtp_server, port, context=context)
    server.ehlo()
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, msg.as_string())
    server.quit()


def get_event_from_data(data):
    """Get event info. Function to ensure modularity if API fails.
    """
    # Get the current event name
    return data["events"][0]["name"]


def get_avail_from_data(data):
    """Get players in field. Function to ensure modularity if API fails.
    """
    # Get the players in the field, who have yet to tee off
    return [
        a["athlete"]["displayName"]
        for a in data["events"][0]["competitions"][0]["competitors"]
        if (a["status"]["period"] <= 1) and (a["status"]["type"]["state"] == "pre")
    ]


def get_tourn_state_from_data(data):
    """Get tournament state. Function to ensure modularity if API fails.
    """
    return data["events"][0]["status"]["type"]["state"]


def live_scores_from_data(data, current_players):
    """Get live scores. Function to ensure modularity if API fails.
    """
    return {
        user["athlete"]["displayName"]: user["linescores"][0]
        for user in data["events"][0]["competitions"][0]["competitors"]
        if user["athlete"]["displayName"] in current_players
    }


def get_earnings_from_data(data, player):
    """Get earnings. Function to ensure modularity if API fails.
    """
    for user in data["events"][0]["competitions"][0]["competitors"]:
        if user["athlete"]["displayName"] == player:
            return user["earnings"]
    return -1


def remove_canceled(data):
    """Remove canceled tournaments from data list.

    """
    return {
        k: [
            event for event in v if event["status"]["type"]["description"] != "Canceled"
        ]
        for k, v in data.items()
    }


def get_event_info():
    """Get event info. Requires access to API.
    """
    try:
        r = requests.get(EVENT_URL)

        data = r.json()
        data = remove_canceled(data)

        event_name = get_event_from_data(data)
        avail_picks = get_avail_from_data(data)
        tournament_state = get_tourn_state_from_data(data)
        return event_name, avail_picks, tournament_state
    except Exception as e:
        print("Issue getting data from ESPN API. Message: {}".format(e))
        return None, None, None


def get_live_scores(current_players):
    """Get live scores. Requires access to API.
    """
    try:
        r = requests.get(EVENT_URL)

        data = r.json()
        data = remove_canceled(data)

        live_scores = live_scores_from_data(data, current_players)
        return live_scores
    except Exception as e:
        print("Issue getting datafrom ESPN API. Message: {}".format(e))
        return None


def get_earnings(player):
    """Get player earnings. Requires access to API.
    """
    # # Column configuration
    # player_col = "PLAYER NAME"
    # pga_earnings_col = "MONEY"
    # non_earnings_col = "TOTAL MONEY"

    # # Loop through PGA and Non-PGA tour Money lists.
    # for M_URL in [PGA_URL, NON_PGA_URL]:
    #     html = requests.get(M_URL).content
    #     df_list = pd.read_html(html)

    #     # Extract the player DF
    #     player_df = df_list[-1]

    #     # Make all text lower string for matching
    #     player_df[player_col] = player_df[player_col].str.lower()

    #     # Make the players a list
    #     registered_players = list(player_df[player_col])

    #     if player.lower() in registered_players:
    #         try:
    #             earnings = list(
    #                 player_df[player_df[player_col] == player.lower()][pga_earnings_col]
    #             )[0]
    #         except Exception as e:
    #             earnings = list(
    #                 player_df[player_df[player_col] == player.lower()][non_earnings_col]
    #             )[0]

    #         # Extract the value
    #         if isinstance(earnings, str):
    #             return int(earnings.replace("$", "").replace(",", ""))
    #         elif isinstance(earnings, float) or isinstance(earnings, int):
    #             return int(earnings)
    try:
        r = requests.get(EVENT_URL)
        data = r.json()
        data = remove_canceled(data)
    except Exception as e:
        print("Issue getting data from ESPN API. Message: {}".format(e))
        send_email(
            "scott.m.kyle@gmail.com", "User Earning Warning", "{}. {}".format(player, e)
        )
        return -1

    try:
        earnings = get_earnings_from_data(data, player)
    except Exception as e:
        send_email(
            "scott.m.kyle@gmail.com", "User Earning Warning", "{}. {}".format(player, e)
        )

    return earnings


def construct_user_table(users, picks, curr_event=None):
    user_dict = {
        "name": [],
        "weekly earnings": [],
        "total earnings": [],
        "strikes left": [],
    }
    for x in picks:
        print(x.event)
        print(curr_event)

    for usr in users:
        user_dict["name"].append(usr.name)
        user_dict["weekly earnings"].append(
            sum(
                [
                    int(x.points)
                    for x in picks
                    if (x.event == curr_event) and (x.name == usr.name)
                ]
            )
        )
        user_dict["strikes left"].append(int(usr.strikes_remaining))
        user_dict["total earnings"].append(
            sum([int(x.points) for x in picks if x.name == usr.name])
        )

    user_df = pd.DataFrame(user_dict)

    user_df.sort_values(["total earnings"], inplace=True, ascending=False)
    user_df["rank"] = user_df["total earnings"].rank(ascending=False).astype(int)

    max_points = user_df["total earnings"].max()
    user_df["dollars back"] = [x - max_points for x in user_df["total earnings"]]

    # Reorder columns
    user_df = user_df[
        [
            "rank",
            "name",
            "weekly earnings",
            "total earnings",
            "dollars back",
            "strikes left",
        ]
    ]

    if curr_event is None:
        user_df.drop(columns=["weekly earnings"], inplace=True)

    return user_df.to_html(classes="data", border=0, index=False)
