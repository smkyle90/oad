from flask_table import Col, Table

import plotly
import plotly.graph_objs as go

import pandas as pd
import numpy as np
import json

from .models import User, Pick

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


def create_plot():
    # raw_picks = {
    #     "user": [1,2,3,1,2,3,1,2,3,1,2,3],
    #     "points": [10, 8, 2, 0, 4, 5, 4, 2, 1, 4,6,4],
    #     "tournament": ["Masters","Masters","Masters","Open","Open","Open","US Open","US Open","US Open","PGA Championship","PGA Championship","PGA Championship",],

    # }

    all_picks = Pick.query.all()

    raw_picks = {}
    raw_picks["user"] = [pick.name if pick.name else "test" for pick in all_picks]
    raw_picks["points"] = [pick.points for pick in all_picks]
    raw_picks["tournament"] = [
        pick.event if pick.name else "test" for pick in all_picks
    ]

    df = pd.DataFrame(raw_picks)

    tournaments = df.tournament.unique()
    users = df.user.unique()
    data = []
    cumulative = {}
    for user in users:
        user_points = df[df.user == user].points
        user_tourns = df[df.user == user].tournament
        data.append(go.Bar(x=user_tourns, y=user_points, name=str(user)))
        user_cum = 0
        cumulative[user] = []
        for tour in tournaments:
            try:
                tour_pts = df[
                    (df.user == user) & (df.tournament == tour)
                ].points.tolist()[0]
                user_cum += tour_pts
            except Exception:
                pass

            cumulative[user].append(user_cum)

    data1 = [
        go.Scatter(mode="lines", x=tournaments, y=user_pts, name=str(user),)
        for user, user_pts in cumulative.items()
    ]

    layout = go.Layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

    fig1 = go.Figure(data=data, layout=layout)
    fig1.update_layout(barmode="group")
    fig2 = go.Figure(data=data1, layout=layout)

    fig1.update_xaxes(showgrid=False, title_text="tourney")
    fig2.update_xaxes(showgrid=False, title_text="tourney")
    fig1.update_yaxes(showgrid=True, title_text="tournament earnings [$]")
    fig2.update_yaxes(showgrid=True, title_text="cumulative earnings [$]")

    g1 = json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder)
    g2 = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)

    return g1, g2
