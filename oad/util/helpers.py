"""App helper functions
"""
import os
import random
import smtplib
import ssl
import string
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


def get_random_password_string(length):
    password_characters = string.ascii_letters + string.digits + string.punctuation[2:6]
    password = "".join(random.choice(password_characters) for i in range(length))
    return password


def send_email(receiver_email, subject, html):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
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


def get_tournament_info(data):
    """Get tournament purse. Function to ensure modularity if API fails.
    """
    courses_separator = ", "

    data_dict = {}

    try:
        data_dict["Purse"] = data["events"][0]["displayPurse"]
    except Exception:
        data_dict["Purse"] = "Unavailable"

    try:
        data_dict["Courses"] = courses_separator.join(
            [course["name"] for course in data["events"][0]["courses"]]
        )
    except Exception:
        data_dict["Courses"] = "Unavailable"
    try:
        data_dict["Defending Champion"] = data["events"][0]["defendingChampion"][
            "athlete"
        ]["displayName"]
    except Exception:
        data_dict["Defending Champion"] = "Unavailable"

    event_dict = {
        "col1": list(data_dict.keys()),
        "col2": list(data_dict.values()),
    }

    df = pd.DataFrame(event_dict)

    return df


def get_tourn_state_from_data(data):
    """Get tournament state. Function to ensure modularity if API fails.
    """
    return data["events"][0]["status"]["type"]["state"]


def live_scores_from_data(data, current_players):
    """Get live scores. Function to ensure modularity if API fails.
    """

    score_data = {}
    rank_data = {}

    for user in data["events"][0]["competitions"][0]["competitors"]:
        player_score = 0
        player_pos = "--"
        for user_score_data in user["linescores"]:
            if user_score_data.get("value"):
                player_pos = user_score_data.get("currentPosition")

            if user["athlete"]["displayName"] in current_players:
                # print(user_score_data)
                if user_score_data.get("value"):
                    try:
                        player_score += int(user_score_data["displayValue"])
                    except Exception as e:
                        player_score += 0

                score_data[user["athlete"]["displayName"]] = {
                    "score": player_score,
                    "position": player_pos,
                    "earnings": int(user.get("earnings", 0)),
                    "freq": 1,
                }

        # Store the number of players at a particular score. This is just the last linescore for each user.
        if rank_data.get(player_pos):
            rank_data[player_pos] += 1
        else:
            rank_data[player_pos] = 1

    for user, vals in score_data.items():
        vals["freq"] = rank_data[vals["position"]]

    return score_data


def get_earnings_from_data(data, player=None):
    """Get earnings. Function to ensure modularity if API fails.
    """
    if player is None:
        return (
            sum(
                [
                    int(user["earnings"])
                    for user in data["events"][0]["competitions"][0]["competitors"]
                ]
            )
            > 0
        )

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
        tournament_info = get_tournament_info(data)

        if tournament_state in ["in", "post"]:
            # check if the earnings are posteds
            earnings_posted = get_earnings_from_data(data)
            if earnings_posted:
                tournament_state = "post"
            else:
                tournament_state = "in"

        return event_name, avail_picks, tournament_state, tournament_info
    except Exception as e:
        print("Issue getting data from ESPN API. Message: {}".format(e))
        return None, None, None, None


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


def get_withdrawl_list():
    try:
        r = requests.get(EVENT_URL)

        data = r.json()
        data = remove_canceled(data)

        all_users = data["events"][0]["competitions"][0]["competitors"]

        withdrawl_list = [
            user["athlete"]["displayName"]
            for user in all_users
            if user["status"]["type"]["description"] == "Withdrawn"
        ]
        return withdrawl_list
    except Exception as e:
        print("Issue getting datafrom ESPN API. Message: {}".format(e))
        return []


def get_earnings(player):
    """Get player earnings. Requires access to API.
    """
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


def format_earnings(val):
    return "${}".format("{:,}".format(int(val)))


def create_pick_table(picks):
    pick_table = {"event": [], "pick": [], "earnings": []}
    for pick in picks:
        pick_table["event"].append(pick.event)
        pick_table["pick"].append(pick.pick)
        pick_table["earnings"].append(pick.points)

    pick_table = pd.DataFrame(pick_table)

    for col in ["earnings"]:
        new_col = [
            format_earnings(val) if val >= 0 else "$ 0" for val in pick_table[col]
        ]
        pick_table[col] = new_col

    pick_table.columns = [x.upper() for x in pick_table.columns]

    return pick_table.to_html(classes="data", border=0, index=False)


def construct_user_table(users, picks, curr_event=None, as_html=True):
    user_dict = {
        "team": [],
        "weekly pick": [],
        "weekly earnings": [],
        "total earnings": [],
        "strikes left": [],
    }

    for usr in users:
        if usr.display_name:
            user_dict["team"].append(usr.display_name)
        else:
            user_dict["team"].append(usr.name)

        weekly_pick = [
            x.pick for x in picks if ((x.event == curr_event) and (x.name == usr.name))
        ]

        if weekly_pick:
            weekly_pick = weekly_pick[0]
        else:
            weekly_pick = "--"

        user_dict["weekly pick"].append(weekly_pick)
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
            "team",
            "weekly pick",
            "weekly earnings",
            "total earnings",
            "dollars back",
            "strikes left",
        ]
    ]

    for col in ["weekly earnings", "total earnings", "dollars back"]:
        new_col = [
            format_earnings(val)
            if val >= 0
            else "-{}".format(format_earnings(abs(val)))
            for val in user_df[col]
        ]
        user_df[col] = new_col

    if curr_event is None:
        user_df.drop(columns=["weekly earnings", "weekly pick"], inplace=True)

    user_df.columns = [x.upper() for x in user_df.columns]

    if as_html:
        return user_df.to_html(classes="data", border=0, index=False)
    else:
        return user_df
