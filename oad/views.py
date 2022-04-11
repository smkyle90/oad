import json
import os

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
    raw_picks["fedex"] = [pick.fedex for pick in all_picks if pick.season == season]
    raw_picks["mult"] = [
        pick.point_multiplier for pick in all_picks if pick.season == season
    ]

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
        user_points = df[df.user == user].fedex * df[df.user == user].mult
        user_tourns = df[df.user == user].tournament
        bar_data.append(go.Bar(x=user_tourns[-5:], y=user_points[-5:], name=str(user)))
        user_cum = 0
        cum_points[user] = []
        for tour in tournaments:
            try:
                tour_user = df[(df.user == user) & (df.tournament == tour)]

                tour_pts = (tour_user.fedex * tour_user.mult).tolist()[0]
                user_cum += tour_pts
            except Exception:
                pass

            cum_points[user].append(user_cum)

    line_data = [
        go.Scatter(
            mode="lines+markers", x=tournaments[-5:], y=user_pts[-5:], name=str(user),
        )
        for user, user_pts in cum_points.items()
    ]

    layout = go.Layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

    br_fig = go.Figure(data=bar_data, layout=layout)
    br_fig.update_layout(barmode="group")
    ln_fig = go.Figure(data=line_data, layout=layout)

    br_fig.update_xaxes(showgrid=False, title_text="tourney")
    ln_fig.update_xaxes(showgrid=False, title_text="tourney")
    br_fig.update_yaxes(showgrid=True, title_text="tournament points")
    ln_fig.update_yaxes(showgrid=True, title_text="cumulative points")

    br_json = json.dumps(br_fig, cls=plotly.utils.PlotlyJSONEncoder)
    ln_json = json.dumps(ln_fig, cls=plotly.utils.PlotlyJSONEncoder)

    return br_json, ln_json
