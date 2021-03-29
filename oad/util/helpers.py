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
        data_dict["Purse"] = "$10,500,000"  # data["events"][0]["displayPurse"]
    except Exception:
        data_dict["Purse"] = "Unavailable"

    try:
        # data_dict["Courses"] = courses_separator.join(
        #     [course["name"] for course in data["events"][0]["courses"]]
        # )
        data_dict["Courses"] = "Austin Country Club"
    except Exception:
        data_dict["Courses"] = "Unavailable"
    try:
        # data_dict["Defending Champion"] = data["events"][0]["defendingChampion"][
        #     "athlete"
        # ]["displayName"]
        data_dict["Defending Champion"] = "Kevin Kisner"
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

    for match in data["events"][0]["competitions"][-1]:
        players = []
        player_score = []
        player_pos = 0
        for player in match["competitors"]:
            players.append(player["athlete"]["displayName"])
            player_score.append(player["score"]["value"])

        for idx, player in enumerate(players):
            if player in current_players:
                if not player_score[idx]:
                    score = player_score[(idx + 1) % 2]
                else:
                    score = -player_score[idx]

                score_data[player] = {
                    "score": score,
                    "position": player_pos,
                    "earnings": 0,
                    "freq": 1,
                    "opponent": players[(idx + 1) % 2],
                }

    return score_data
    # for user in data["events"][0]["competitions"][0]["competitors"]:
    #     player_score = 0
    #     player_pos = "--"
    #     for user_score_data in user["linescores"]:
    #         if user_score_data.get("value"):
    #             player_pos = user_score_data.get("currentPosition")

    #         if user["athlete"]["displayName"] in current_players:
    #             # print(user_score_data)
    #             if user_score_data.get("value"):
    #                 try:
    #                     player_score += int(user_score_data["displayValue"])
    #                 except Exception as e:
    #                     player_score += 0

    #             score_data[user["athlete"]["displayName"]] = {
    #                 "score": player_score,
    #                 "position": player_pos,
    #                 "earnings": int(user.get("earnings", 0)),
    #                 "freq": 1,
    #             }

    #     # Store the number of players at a particular score. This is just the last linescore for each user.
    #     if rank_data.get(player_pos):
    #         rank_data[player_pos] += 1
    #     else:
    #         rank_data[player_pos] = 1

    # for user, vals in score_data.items():
    #     vals["freq"] = rank_data[vals["position"]]

    # return score_data


def get_earnings_from_data(data, player=None):
    """Get earnings. Function to ensure modularity if API fails.
    """
    if player is None:
        try:
            return (
                sum(
                    [
                        int(user["earnings"])
                        for user in data["events"][0]["competitions"][0]["competitors"]
                    ]
                )
                > 0
            )
        except Exception as e:
            print(e)
            return False

    try:
        for user in data["events"][0]["competitions"][0]["competitors"]:
            if user["athlete"]["displayName"] == player:
                return user["earnings"]
    except Exception as e:
        print(e)
        return False

    return False


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

        # event_name = get_event_from_data(data)
        # avail_picks = get_avail_from_data(data)
        tournament_state = get_tourn_state_from_data(data)
        tournament_info = get_tournament_info(data)

        # DIRTY HACK FOR WGC
        event_name = "WGC Dell Technologies Match Play"
        avail_picks = [
            "Justin Thomas",
            "Bryson DeChambeau",
            "Dustin Johnson",
            "Jon Rahm",
            "Rory McIlroy",
            "Collin Morikawa",
            "Patrick Reed",
            "Jordan Spieth",
            "Patrick Cantlay",
            "Viktor Hovland",
            "Xander Schauffele",
            "Paul Casey",
            "Tony Finau",
            "Sungjae Im",
            "Webb Simpson",
            "Daniel Berger",
            "Tyrrell Hatton",
            "Sergio Garcia",
            "Matt Fitzpatrick",
            "Cameron Smith",
            "Hideki Matsuyama",
            "Louis Oosthuizen",
            "Joaquin Niemann",
            "Jason Day",
            "Tommy Fleetwood",
            "Will Zalatoris",
            "Scottie Scheffler",
            "Abraham Ancer",
            "Lee Westwood",
            "Corey Conners",
            "Christiaan Bezuidenhout",
            "Jason Kokrak",
            "Kevin Kisner",
            "Russell Henley",
            "Max Homa",
            "Harris English",
            "Si Woo Kim",
            "Brian Harman",
            "Billy Horschel",
            "Ryan Palmer",
            "Kevin Na",
            "Bubba Watson",
            "Matt Wallace",
            "Marc Leishman",
            "Matthew Wolff",
            "Ian Poulter",
            "Brendon Todd",
            "Lanto Griffin",
            "Carlos Ortiz",
            "Shane Lowry",
            "Victor Perez",
            "Matt Kuchar",
            "Talor Gooch",
            "Kevin Streelman",
            "Robert MacIntyre",
            "Erik van Rooyen",
            "Dylan Frittelli",
            "Antoine Rozner",
            "Sebastian Munoz",
            "Mackenzie Hughes",
            "J.T. Poston",
            "Bernd Wiesberger",
            "Adam Long",
            "Andy Sullivan",
        ]

        if tournament_state in ["in", "post"]:
            # check if the earnings are posteds
            earnings_posted = get_earnings_from_data(data)
            if earnings_posted:
                tournament_state = "post"
            else:
                tournament_state = "in"

        tournament_state = "post"
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
    # """
    # try:
    #     r = requests.get(EVENT_URL)
    #     data = r.json()
    #     data = remove_canceled(data)
    # except Exception as e:
    #     print("Issue getting data from ESPN API. Message: {}".format(e))
    #     send_email(
    #         "scott.m.kyle@gmail.com", "User Earning Warning", "{}. {}".format(player, e)
    #     )
    #     return -1

    # try:
    #     earnings = get_earnings_from_data(data, player)
    # except Exception as e:
    #     send_email(
    #         "scott.m.kyle@gmail.com", "User Earning Warning", "{}. {}".format(player, e)
    #     )

    # WGC
    tourn_earnings = {
        "Billy Horschel": 1820000,
        "Scottie Scheffler": 1150000,
        "Matt Kuchar": 740000,
        "Victor Perez": 600000,
        "Tommy Fleetwood": 337000,
        "Sergio Garcia": 337000,
        "Jon Rahm": 337000,
        "Brian Harman": 337000,
        "Dylan Frittelli": 189000,
        "Kevin Streelman": 189000,
        "Mackenzie Hughes": 189000,
        "Robert MacIntyre": 189000,
        "Ian Poulter": 189000,
        "Erik von Rooyen": 189000,
        "Bubba Watson": 189000,
        "Jordan Spieth": 189000,
        "Ryan Palmer": 144000,
        "Kevin Kisner": 113700,
        "Max Homa": 113700,
        "Antoine Rozner": 113700,
        "Xander Schauffele": 113700,
        "Joaquin Niemann": 113700,
        "Lee Westwood": 113700,
        "Patrick Cantlay": 113700,
        "Abraham Ancer": 113700,
        "Daniel Berger": 113700,
        "Matt Fitzpatrick": 113700,
        "Dustin Johnson": 75000,
        "Adam Long": 75000,
        "J.T. Poston": 75000,
        "Patrick Reed": 75000,
        "Matt Wallace": 75000,
        "Webb Simpson": 75000,
        "Paul Casey": 75000,
        "Rory McIlroy": 75000,
        "Cameron Smith": 75000,
        "Tony Finau": 75000,
        "Will Zalatoris": 75000,
        "Matthew Wolff": 75000,
        "Marc Leishman": 75000,
        "Russell Henley": 75000,
        "Kevin Na": 47571.43,
        "Justin Thomas": 47571.43,
        "Shane Lowry": 47571.43,
        "Bryson DeChambeau": 47571.43,
        "Jason Day": 47571.43,
        "Andy Sullivan": 47571.42,
        "Carlos Ortiz": 47571.43,
        "Hideki Matsuyama": 47571.43,
        "Jason Kokrak": 47571.43,
        "Bernd Wiesberger": 47571.43,
        "Viktor Hovland": 47571.43,
        "Harris English": 47571.43,
        "Brendon Todd": 47571.42,
        "Sungjae Im": 47571.43,
        "Collin Morikawa": 38000,
        "Si Woo Kim": 38000,
        "Christiaan Bezuidenhout": 38000,
        "Tyrrell Hatton": 38000,
        "Talor Gooch": 38000,
        "Louis Oosthuizen": 35750,
        "Sebastian Munoz": 35750,
        "Lanto Griffin": 35750,
        "Corey Conners": 35750,
    }
    earnings = tourn_earnings.get(player)

    print(player, earnings)
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
