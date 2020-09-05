"""Scheduled Tasks each week.
"""

from flask import session

from .helpers import get_earnings, get_event_info
from .models import Pick, Player, User


def send_pick_reminder():
    return


def send_picks():
    """Send the picks for the week.
    """
    return


def send_weekly_update():
    """Send a weekly summary.
    """
    return

def set_state():
    """Set the session variables.
    """
    event_name, __, tournament_state = get_event_info()

    print ("Setting {} State to {}.".format(event_name, tournament_state))
    session["event_state"] = tournament_state
    session["name"] = event_name
    session.modified =  True

