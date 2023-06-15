"""App helper functions
"""
import json
import os
import random
import smtplib
import ssl
import string
import time
from email.mime.text import MIMEText

import pandas as pd
import requests

from .. import redis_cache

"""
https://pthree.org/2012/01/07/encrypted-mutt-imap-smtp-passwords/
https://gist.github.com/bnagy/8914f712f689cc01c267
"""

EVENT_TYPE = "major"

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, "points.csv")
POINTS_DF = pd.read_csv(filename)

EVENT_URL = (
    "https://site.web.api.espn.com/apis/site/v2/sports/golf/leaderboard?league=pga"
)

PGA_URL = "https://www.pgatour.com/stats/stat.109.html"
NON_PGA_URL = "https://www.pgatour.com/stats/stat.02677.html"

# Ping API at most every UDPATE_TIME seconds
UPDATE_TIME = 60


def check_rule_status(user, current_event):
    # Check the user has not used their rules.

    strike_used = bool(user.strike_event)
    tap_in_used = bool(user.substitute_event)
    double_up_used = bool(user.double_up_event)

    if user.strike_event == current_event:
        tap_in_used = True
        double_up_used = True

    if user.substitute_event == current_event:
        strike_used = True
        double_up_used = True

    if user.double_up_event == current_event:
        strike_used = True
        tap_in_used = True

    return strike_used, tap_in_used, double_up_used


def get_random_password_string(length):
    password_characters = string.ascii_letters + string.digits + string.punctuation[2:6]
    password = "".join(random.choice(password_characters) for i in range(length))
    return password


def send_email(receiver_email, subject, html):
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "1993oad@gmail.com"
    password = os.getenv("OADPW")

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


def get_tournament_round(data):
    try:
        tournament_round = int(data["events"][0]["competitions"][0]["status"]["period"])
    except Exception:
        tournament_round = 0

    return tournament_round


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
        if (a["status"]["period"] <= 2) and (a["status"]["type"]["state"] == "pre")
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

        # Deal with players who have WD after starting
        if user["status"].get("displayValue", False) == "WD":
            continue

        for idx, user_score_data in enumerate(user["linescores"]):
            if user_score_data.get("value"):
                player_pos = user_score_data.get("currentPosition")

            if user["athlete"]["displayName"] in current_players:
                if user_score_data.get("value"):
                    try:
                        player_score += int(user_score_data["displayValue"])
                    except Exception:
                        player_score += 0

                score_data[user["athlete"]["displayName"]] = {
                    "score": player_score,
                    "position": player_pos,
                    "earnings": int(user.get("earnings", 0)),
                    "points": -1,
                    "freq": 1,
                    "round": idx + 1,
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


def update_weekly_pick_table(users, week_picks, event_table, user_table):
    picks_last_update = redis_cache.get("picks_last_update")
    if picks_last_update is None:
        picks_last_update = 0
    picks_last_update = float(picks_last_update)

    if time.time() - picks_last_update > UPDATE_TIME:
        pick_table = weekly_pick_table(users, week_picks, event_table, user_table)

        redis_cache.set(
            "pick_table", pick_table.to_html(classes="data", border=0, index=False)
        )
        redis_cache.set("picks_last_update", time.time())

        pick_list = pick_table["PICK"].tolist()

        try:
            points_list = pick_table["PROJ. POINTS"]
        except Exception:
            points_list = pick_table["POINTS"]

        normalised_points_list = [
            float(p) / float(m) if m else 0
            for p, m in zip(points_list.to_list(), pick_table["MULT"].to_list())
        ]

        fedex_pts = {}
        for pick, pts in zip(pick_list, normalised_points_list):
            fedex_pts[pick] = pts

        redis_cache.set("pick_points", json.dumps(fedex_pts))


def get_weekly_pick_table():
    return redis_cache.get("pick_table").decode()


def update_cache_from_api():
    """
    Make a single API call and update the cache. We use this info to do our
    calculations
    """
    api_last_update = redis_cache.get("api_last_update")

    if api_last_update is None:
        api_last_update = 0

    api_last_update = float(api_last_update)

    if time.time() - api_last_update > UPDATE_TIME:
        r = requests.get(EVENT_URL)
        data = r.json()
        data = remove_canceled(data)
        data = json.dumps(data)
        redis_cache.set("data", data)
        redis_cache.set("api_last_update", time.time())


def get_event_info():
    """Get event info. Requires access to API.
    """
    try:
        data = redis_cache.get("data")
        data = json.loads(data)

        event_name = get_event_from_data(data)
        avail_picks = get_avail_from_data(data)
        tournament_state = get_tourn_state_from_data(data)
        tournament_info = get_tournament_info(data)
        tournament_round = get_tournament_round(data)

        if tournament_state in ["in", "post"]:
            # check if the earnings are posteds
            earnings_posted = get_earnings_from_data(data)
            if earnings_posted:
                tournament_state = "post"
            else:
                tournament_state = "in"

        return (
            event_name,
            avail_picks,
            tournament_state,
            tournament_info,
            tournament_round,
        )
    except Exception as e:
        print("Issue getting data from ESPN API. Message: {}".format(e))
        return None, None, None, None, None


def get_live_scores(current_players):
    """Get live scores. Requires access to API.
    """
    try:
        data = redis_cache.get("data")
        data = json.loads(data)
        live_scores = live_scores_from_data(data, current_players)
        return live_scores
    except Exception as e:
        print("Issue getting datafrom ESPN API. Message: {}".format(e))
        return None


def get_withdrawl_list():
    try:
        data = redis_cache.get("data")
        data = json.loads(data)

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
        data = redis_cache.get("data")
        data = json.loads(data)
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


def get_fedex_points(player):
    fedex_pts = redis_cache.get("pick_points")

    if fedex_pts is None:
        fedex_pts = {}

    fedex_pts = json.loads(fedex_pts)

    return fedex_pts.get(player, -1)


def format_earnings(val):
    return "${}".format("{:,}".format(int(val)))


def create_pick_table(picks):
    pick_table = {
        "event": [],
        "pick": [],
        "points": [],
        "earnings": [],
        "multiplier": [],
    }
    for pick in picks:
        pick_table["event"].append(pick.event)
        pick_table["pick"].append(pick.pick)
        pick_table["points"].append(round(pick.fedex))
        pick_table["earnings"].append(pick.points)
        pick_table["multiplier"].append(pick.point_multiplier)

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
        "total points": [],
        "weekly points": [],
        "breakfast balls left": [],
        "tap-ins left": [],
        "double-ups left": [],
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
            weekly_pick = " ".join(weekly_pick)
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
        user_dict["weekly points"].append(
            int(
                sum(
                    [
                        x.fedex * x.point_multiplier
                        for x in picks
                        if (x.event == curr_event) and (x.name == usr.name)
                    ]
                )
            )
        )
        user_dict["breakfast balls left"].append(int(usr.strikes_remaining))
        user_dict["tap-ins left"].append(int(usr.substitutes_remaining))
        user_dict["double-ups left"].append(int(usr.double_up_remaining))
        user_dict["total earnings"].append(
            sum([int(x.points) for x in picks if x.name == usr.name])
        )
        user_dict["total points"].append(
            int(
                sum([x.fedex * x.point_multiplier for x in picks if x.name == usr.name])
            )
        )

    user_df = pd.DataFrame(user_dict)

    user_df.sort_values(["total points"], inplace=True, ascending=False)
    user_df["rank"] = user_df["total points"].rank(ascending=False).astype(int)

    max_earnings_delta = user_df["total earnings"].max()
    user_df["dollars back"] = [
        x - max_earnings_delta for x in user_df["total earnings"]
    ]

    max_points_delta = user_df["total points"].max()
    user_df["points back"] = [x - max_points_delta for x in user_df["total points"]]

    # Reorder columns
    user_df = user_df[
        [
            "rank",
            "team",
            "weekly pick",
            "weekly earnings",
            "total earnings",
            "dollars back",
            "weekly points",
            "total points",
            "points back",
            "breakfast balls left",
            "tap-ins left",
            "double-ups left",
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
        user_df.drop(
            columns=[
                "weekly earnings",
                "weekly pick",
                "weekly points",
                "total earnings",
                "dollars back",
            ],
            inplace=True,
        )

    user_df.columns = [x.upper() for x in user_df.columns]

    if as_html:
        return user_df.to_html(classes="data", border=0, index=False)
    else:
        return user_df


# flake8: noqa: C901
def weekly_pick_table(users, picks, event_info, user_data):
    # get purse value
    try:
        purse_value = event_info.loc[event_info.col1 == "Purse", "col2"].iloc[0][1:]
        purse_value = float(purse_value.replace(",", ""))
    except Exception as e:
        print(e)
        purse_value = 11, 500, 000

    # construct user dict for display names
    user_dict = {
        user.name: user.display_name if user.display_name else user.name
        for user in users
    }

    rules_dict = {
        user_dict[user.name]: (
            user.strike_event,
            user.substitute_event,
            user.double_up_event,
        )
        for user in users
    }

    rules = {
        0: "brekky ball",
        1: "tap-in",
        2: "double-up",
    }

    pick_dict = {
        "team": [user_dict[p.name] for p in picks if p.point_multiplier],
        "initials": [
            "".join([w[0] for w in p.name.split(" ") if w])
            for p in picks
            if p.point_multiplier
        ],
        "pick": [p.pick for p in picks if p.point_multiplier],
        "points": [0 for p in picks if p.point_multiplier],
        "alternate": [p.alternate for p in picks if p.point_multiplier],
        "tot": [],
        "pos": [],
        "points": [],
        "earnings": [],
        "helpers": [],
        "mult": [p.point_multiplier for p in picks if p.point_multiplier],
    }

    # live scores from API for each pick.
    live_scores = get_live_scores(
        set(pick_dict["pick"]).union(set(pick_dict["alternate"]))
    )

    curr_event, _, _, _, curr_round = get_event_info()

    # Add the projected fedex points for this event
    for pick in live_scores:
        try:
            fedex_pts = round(
                POINTS_DF[EVENT_TYPE]
                .loc[
                    (live_scores[pick]["position"] - 1) : (
                        live_scores[pick]["position"] - 1
                    )
                    + (live_scores[pick]["freq"] - 1)
                ]
                .sum()
                / (live_scores[pick]["freq"]),
                0,
            )
        except Exception as e:
            print(e)
            fedex_pts = 0
        if curr_round <= 2:
            in_play = True
        elif curr_round <= 4:
            in_play = live_scores.get(pick, {}).get("round", 0) == curr_round
        else:
            in_play = live_scores.get(pick, {}).get("round", 0) >= curr_round - 1

        if in_play:
            live_scores[pick]["points"] = fedex_pts
        else:
            live_scores[pick]["points"] = 0

    # extract the user data for use in the table
    current_points = {
        user: (points, rank)
        for user, points, rank in zip(
            user_data["TEAM"], user_data["TOTAL POINTS"], user_data["RANK"]
        )
    }

    # get missing picks
    all_users = set(current_points.keys())
    curr_users = set(pick_dict["team"])
    missing_picks = all_users - curr_users

    for missed in missing_picks:
        pick_dict["team"].append(missed)
        pick_dict["pick"].append("--")
        pick_dict["alternate"].append("--")
        pick_dict["mult"].append(0)
        pick_dict["initials"].append("--")

    for idx, pick in enumerate(pick_dict["pick"]):
        if pick not in live_scores:
            pick = pick_dict["alternate"][idx]
            pick_dict["pick"][idx] = pick

        try:
            in_play = live_scores.get(pick, {}).get("round", 0) == curr_round
        except Exception as e:
            in_play = False

        try:
            pick_dict["tot"].append(live_scores[pick]["score"])
            pick_dict["pos"].append(live_scores[pick]["position"])
            pick_dict["points"].append(live_scores[pick]["points"])
            pick_dict["earnings"].append(live_scores[pick]["earnings"])
        except Exception as e:
            pick_dict["tot"].append(1000)
            pick_dict["pos"].append(1000)
            pick_dict["points"].append(0)
            pick_dict["earnings"].append(0)

    for team in pick_dict["team"]:
        rule_used = False
        for idx, x in enumerate(rules_dict.get(team, ())):
            if x == curr_event:
                pick_dict["helpers"].append(rules.get(idx))
                rule_used = True

        if not rule_used:
            pick_dict["helpers"].append("--")

    if len(pick_dict["helpers"]) != len(pick_dict["team"]):
        pick_dict["helpers"] = ["--" for _ in pick_dict["team"]]

    df = pd.DataFrame(pick_dict)
    df.sort_values(["pos", "pick", "team"], inplace=True, ascending=True)

    # Format the score
    df["tot"] = ["+{}".format(score) if score > 0 else score for score in df["tot"]]
    df["tot"] = ["E" if not score else score for score in df["tot"]]

    try:
        df.replace({"tot": {"+1000": "--"}, "pos": {1000: "--"}}, inplace=True)
    except Exception as e:
        print(e)

    # current rank
    df["pr"] = [int(current_points.get(row.team)[1]) for row in df.itertuples()]

    # Display table based on if points are published
    if df["earnings"].sum():
        df["pos"] = df["pos"].fillna(-1)
        try:
            df.replace({"pos": {"--": -1}}, inplace=True)
        except Exception as e:
            print(e)

        df["pos"] = df["pos"].astype(int)
        df["pos"] = df["pos"].replace(-1, "CUT/NO PICK")

        df.points *= df.mult
        df.points = df.points.astype(int)

        df["points"] = [round(points) for points in df["points"]]
        df["earnings"] = [format_earnings(earnings) for earnings in df["earnings"]]

        df = df[["team", "pick", "tot", "pos", "points", "earnings", "helpers", "mult"]]

    else:  # In tournament display
        df.points *= df.mult
        df.points = df.points.astype(int)

        # Future earning
        df["fp"] = [
            int(current_points.get(row.team)[0]) + row.points for row in df.itertuples()
        ]

        # Future rank
        df["fr"] = df["fp"].rank(ascending=False).astype(int)

        # calculate projected points
        df["proj. points"] = ["{}".format(round(points, 0)) for points in df["points"]]

        # Calculate the rank delta and display
        df["dr"] = df.pr - df.fr
        dr_res = []
        for delta in df["dr"]:
            if delta > 0:
                dr_res.append("▲{}".format(delta))
            elif not delta:
                dr_res.append("--")
            else:
                dr_res.append("▼{}".format(-delta))

        df["dr"] = dr_res
        df["proj. rank"] = df[["fr", "dr"]].apply(
            lambda x: "{} ({})".format(x[0], x[1]), axis=1
        )

        df = df[
            [
                "team",
                "pick",
                "tot",
                "pos",
                "proj. points",
                "proj. rank",
                "helpers",
                "mult",
                "initials",
            ]
        ]

    df.columns = [x.upper() for x in df.columns]

    return df
