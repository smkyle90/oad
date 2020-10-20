"""Admin actions.
"""

from .. import db
from ..models import Pick, Player
from . import get_earnings


def update_player_earnings():
    """Update the player earnings in the player DB with their
    updated TOTAL MONEY (or MONEY)
    """
    all_players = Player.query.all()

    for player in all_players:
        curr_earnings = get_earnings(player.name)
        player.cumulative_points = curr_earnings
        # Commit the changes
        db.session.commit()


def add_user_points():
    """Add the user points for their pick.
    """
    # Get the picks for the week
    picks = Pick.query.filter(Pick.points < 0).all()

    for pick in picks:
        # Get the golfer's name
        player_name = pick.pick
        weekly_earnings = get_earnings(player_name)

        # Update the pick with this value
        pick.points = weekly_earnings

        # Commit the changes
        db.session.commit()
