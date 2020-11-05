import json

import pandas as pd
import plotly
import plotly.graph_objs as go
from flask_table import Col, Table

from .models import Pick
from .util import get_live_scores


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
        "score": [],
        "position": [],
    }

    for k, v in user_scores.items():
        live_scores["pick"].append(k)
        live_scores["user"].append(v[0])
        live_scores["score"].append(v[1])
        live_scores["position"].append(v[2])

    df = pd.DataFrame(live_scores)

    df.sort_values(["position"], inplace=True, ascending=True)

    # Reorder columns
    df = df[["user", "pick", "score", "position"]]

    return df.to_html(classes="data", border=0, index=False)


def league_page():
    all_picks = Pick.query.all()

    raw_picks = {}
    raw_picks["user"] = [pick.name for pick in all_picks]
    raw_picks["player"] = [pick.pick for pick in all_picks]
    raw_picks["points"] = [pick.points for pick in all_picks]
    raw_picks["tournament"] = [pick.event for pick in all_picks]

    pick_history = pick_matrix(raw_picks)
    # best = best_picks(raw_picks)
    bar_plot, line_plot = create_plots(raw_picks)

    return pick_history, bar_plot, line_plot


def player_picks(raw_picks):
    """Picks per player.
    """
    df = pd.DataFrame(raw_picks)

    df_user = pd.pivot_table(
        df,
        values="player",
        index=["tournament"],
        columns=["user"],
        fill_value="--",
        aggfunc="first",
    )

    return df_user


def pick_matrix(raw_picks):
    """For each player, show which player has picked them.

    Args:
        df

    Returns:
        df

    """
    df = player_picks(raw_picks)

    # df = df[df.max(axis=1) > -1]

    # df.replace(-1, "avail", inplace=True)
    # df.replace(-1e-9, "in play", inplace=True)

    # df = df.drop(columns=["user", "tournament", "points"]).dropna()
    # df.sort_values(["player"], inplace=True)

    return df.to_html(classes="data", border=0, index=False)


def best_picks(raw_picks):
    """For each player, show who made the most money over the field.

    Args:
        df

    Returns:
        df

    """

    df = player_picks(raw_picks)

    players = df.player
    df = df.drop(columns=["player"])
    df.replace(-1, -1e-9, inplace=True)

    df = (
        df.sub(df.mean(axis=1), axis=0)
        .div(df.std(axis=1), axis=0)
        .div(df.std(axis=1), axis=0)
    )
    df.fillna(0)

    df.astype(int)

    df.insert(0, "player", players)

    return df.to_html(classes="data", border=0, index=False)


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
        go.Scatter(mode="lines", x=tournaments[-5:], y=user_pts[-5:], name=str(user),)
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
