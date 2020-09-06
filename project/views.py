from flask_table import Col, Table

import plotly
import plotly.graph_objs as go

import pandas as pd
import numpy as np
import json


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
    cumulative_points = Col("cumulative_points")


class UserPickTable(Table):
    event = Col("event")
    pick = Col("pick")
    points = Col("points")


def create_plot():
    data = go.Bar(
            x=['Sivaranjani S', 'Vijayalakshmi C', 'Rajeshwari S', 'Shanthi Priscilla', 'Pandiyaraj G', 'Kamatchi S', 'MohanaPriya', 'Madhumitha G', 'Franklin Alphones Raj J', 'Akfaris Almaas', 'Biswajit Champati', 'Priya R', 'Rekha Rajasekaran', 'Sarath Kumar B', 'Jegan L', 'Karthick A', 'Mahalakshmi S', 'Ragunathan V', 'Anu S', 'Ramkumar KS', 'Uthra R'],
            y=[1640, 1394, 1390, 1313, 2166, 1521, 1078, 1543, 780, 1202, 1505, 2028, 2032, 1769, 1238, 1491, 1477, 1329, 2038, 1339, 1458],
            text=['Scuti', 'Scuti', 'Cygni', 'Scorpii', 'Scuti', 'Pollux', 'Scorpii', 'Pollux', 'Scuti', 'Pollux', 'Scorpii', 'Scorpii', 'Scuti', 'Cygni', 'Scorpii', 'Scuti', 'Scuti', 'Pollux', 'Scuti', 'Pollux', 'Pollux']
        )

    layout = go.Layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    fig = go.Figure(data=data, layout=layout)

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON