import json

import pandas as pd
import plotly
import plotly.graph_objs as go
from flask_table import Col, Table

from .models import Pick
from .util import format_earnings, get_live_scores, pos_payouts


class Earnings(Col):
    def td_format(self, content):
        if content < 0:
            return "--"
        else:
            return int(content)


# Declare your table
class UserTable(Table):
    name = Col("name")
    strikes_remaining = Col("strikes_remaining")


# Declare your table
class PickTable(Table):
    # event = Col("event")
    name = Col("name")
    pick = Col("pick")


# Declare your table
class PlayerTable(Table):
    name = Col("name")
    cumulative_points = Earnings("cumulative_points")


class UserPickTable(Table):
    event = Col("event")
    pick = Col("pick")
    points = Earnings("points")


def weekly_pick_table(users, picks, event_info, user_data):
    # get purse value
    purse_value = event_info.loc[event_info.col1 == "Purse", "col2"].iloc[0][1:]
    purse_value = float(purse_value.replace(",", ""))

    # construct user dict for display names
    user_dict = {
        user.name: user.display_name if user.display_name else user.name
        for user in users
    }

    pick_dict = {
        "team": [user_dict[p.name] for p in picks],
        "pick": [p.pick for p in picks],
        "pe": [0 for p in picks],
        "alternate": [p.alternate for p in picks],
        "tot": [],
        "pos": [],
        "earnings": [],
    }
    # live scores from API for each pick.
    live_scores = get_live_scores(
        set(pick_dict["pick"]).union(set(pick_dict["alternate"]))
    )

    for idx, pick in enumerate(pick_dict["pick"]):

        if pick not in live_scores:
            pick = pick_dict["alternate"][idx]
            pick_dict["pick"][idx] = pick

        try:
            pick_dict["tot"].append(live_scores[pick]["score"])
        except Exception as e:
            print(e)
            pick_dict["tot"].append("--")

        try:
            pick_dict["pos"].append(live_scores[pick]["position"])
        except Exception as e:
            print(e)
            pick_dict["pos"].append("--")

        try:
            pick_dict["earnings"].append(live_scores[pick]["earnings"])
        except Exception as e:
            print(e)
            pick_dict["earnings"].append(0)

    # calculate projected earnings
    try:
        pot_earns = []
        for pick in pick_dict["pick"]:
            try:
                pot_earns.append(
                    (purse_value / 100)
                    * sum(
                        pos_payouts[
                            live_scores[pick]["position"]
                            - 1 : (live_scores[pick]["position"] - 1)
                            + live_scores[pick]["freq"]
                        ]
                    )
                    / (live_scores[pick]["freq"])
                )
            except Exception:
                pot_earns.append(0)
        pick_dict["pe"] = pot_earns
    except Exception as e:
        print("pe", e)
        pick_dict["pe"] = [0 for pick in pick_dict["pick"]]

    # extract the user data for use in the table
    current_earnings = {
        user: (float(earnings.replace("$", "").replace(",", "")), rank)
        for user, earnings, rank in zip(
            user_data["TEAM"], user_data["TOTAL EARNINGS"], user_data["RANK"]
        )
    }

    # make pick dataframe
    df = pd.DataFrame(pick_dict)
    df.sort_values(["pos", "pick", "team"], inplace=True, ascending=True)

    # get missing picks
    all_users = set(current_earnings.keys())
    curr_users = set(df.team)
    missing_picks = all_users - curr_users

    # Format the score
    df["tot"] = ["+{}".format(score) if score > 0 else score for score in df["tot"]]
    df["tot"] = ["E" if not score else score for score in df["tot"]]

    # current rank
    df["pr"] = [int(current_earnings.get(row.team)[1]) for row in df.itertuples()]

    # Display table based on if earnings are published
    if df["earnings"].sum():
        df["pos"] = df["pos"].fillna(-1)
        df["pos"] = df["pos"].astype(int)
        df["pos"] = df["pos"].replace(-1, "CUT")

        df["earnings"] = [format_earnings(earnings) for earnings in df["earnings"]]

        df = df[["team", "pick", "tot", "pos", "earnings"]]

    else:  # In tournament display
        # Future earning
        df["fe"] = [
            int(current_earnings.get(row.team)[0]) + row.pe for row in df.itertuples()
        ]
        # Future rank
        df["fr"] = df["fe"].rank(ascending=False).astype(int)

        # calculate projected earnings
        df["proj. earns"] = [
            "${}m".format(round(earnings / 1e6, 2))
            if earnings > 1e6
            else "${}k".format(round(earnings / 1e3))
            for earnings in df["pe"]
        ]
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

        df = df[["team", "pick", "tot", "pos", "proj. earns", "proj. rank"]]

    df.columns = [x.upper() for x in df.columns]

    return df.to_html(classes="data", border=0, index=False)


def live_scores(picks):
    user_scores = {pick.pick: [pick.name] for pick in picks}
    live_scores = get_live_scores(list(user_scores.keys()))
    for k, v in live_scores.items():
        user_scores[k].append(v["displayValue"])
        user_scores[k].append(v["currentPosition"])

    live_scores = {
        "user": [],
        "pick": [],
        "tot": [],
        "position": [],
    }

    for k, v in user_scores.items():
        live_scores["pick"].append(k)
        live_scores["user"].append(v[0])
        live_scores["tot"].append(v[1])
        live_scores["position"].append(v[2])

    df = pd.DataFrame(live_scores)

    df.sort_values(["position"], inplace=True, ascending=True)

    # Reorder columns
    df = df[["user", "pick", "tot", "position"]]

    return df.to_html(classes="data", border=0, index=False)


def league_page(users, season):
    all_picks = Pick.query.all()

    user_dict = {
        user.name: user.display_name if user.display_name else user.name
        for user in users
    }

    raw_picks = {}
    raw_picks["user"] = [
        user_dict[pick.name] for pick in all_picks if pick.season == season
    ]
    raw_picks["player"] = [pick.pick for pick in all_picks if pick.season == season]
    raw_picks["points"] = [pick.points for pick in all_picks if pick.season == season]
    raw_picks["tournament"] = [
        pick.event for pick in all_picks if pick.season == season
    ]

    pick_history = pick_matrix(raw_picks)
    # best = best_picks(raw_picks)
    bar_plot, line_plot = create_plots(raw_picks)

    return pick_history, bar_plot, line_plot


def pick_matrix(raw_picks):
    """For each player, show which player has picked them.

    Args:
        df

    Returns:
        df

    """

    tourn_dict = {}
    t_no = 1
    for tourn in raw_picks["tournament"]:
        if tourn not in tourn_dict:
            tourn_dict[tourn] = t_no
            t_no += 1

    df = pd.DataFrame(raw_picks)
    df = df[df.points >= 0]

    all_users = df.user.unique()
    all_tourns = df.tournament.unique()
    data_dict = {col: [] for col in df.columns}

    for user in all_users:
        for tournament in all_tourns:
            df_filt = df[(df["user"] == user) & (df["tournament"] == tournament)]

            if not len(df_filt):
                continue

            for col in df_filt.columns:
                if col == "player":
                    # We concatenate the entries
                    data_dict[col].append(", ".join(df_filt[col].astype(str).to_list()))
                else:
                    # We just take the first value
                    data_dict[col].append(df_filt[col].iloc[0])

    df = pd.DataFrame(data_dict)

    df["tour_no"] = [tourn_dict[tourn] for tourn in df.tournament]

    df_user = pd.pivot_table(
        df,
        values="player",
        index=["tour_no", "tournament"],
        columns=["user"],
        fill_value="--",
        aggfunc="first",
    )

    # df.columns = [col.upper() for col in df.columns]
    df_user.index.names = None, None

    return df_user.to_html(classes="data", border=0, index=True)


def create_plots(raw_picks):
    df = pd.DataFrame(raw_picks)
    tournaments = df.tournament.unique()
    users = df.user.unique()

    bar_data = []
    cum_points = {}
    for user in users:
        user_points = df[df.user == user].points
        user_tourns = df[df.user == user].tournament
        bar_data.append(go.Bar(x=user_tourns[-5:], y=user_points[-5:], name=str(user)))
        user_cum = 0
        cum_points[user] = []
        for tour in tournaments:
            try:
                tour_pts = df[
                    (df.user == user) & (df.tournament == tour)
                ].points.tolist()[0]
                user_cum += tour_pts
            except Exception:
                pass

            cum_points[user].append(user_cum)

    line_data = [
        go.Scatter(
            mode="lines+markers", x=tournaments[-3:], y=user_pts[-3:], name=str(user),
        )
        for user, user_pts in cum_points.items()
    ]

    layout = go.Layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

    br_fig = go.Figure(data=bar_data, layout=layout)
    br_fig.update_layout(barmode="group")
    ln_fig = go.Figure(data=line_data, layout=layout)

    br_fig.update_xaxes(showgrid=False, title_text="tourney")
    ln_fig.update_xaxes(showgrid=False, title_text="tourney")
    br_fig.update_yaxes(showgrid=True, title_text="tournament earnings [$]")
    ln_fig.update_yaxes(showgrid=True, title_text="cumulative earnings [$]")

    br_json = json.dumps(br_fig, cls=plotly.utils.PlotlyJSONEncoder)
    ln_json = json.dumps(ln_fig, cls=plotly.utils.PlotlyJSONEncoder)

    return br_json, ln_json
