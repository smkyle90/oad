"""Admin actions.
"""

from .. import db
from ..models import Pick, Player
from . import get_earnings, get_withdrawl_list


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

    withdrawl_list = get_withdrawl_list()

    for pick in picks:
        # Get the golfer's name
        player_name = pick.pick

        if player_name in withdrawl_list:
            print("User withdrawn {}".format(player_name))

            # They have withdrawn and thus earn 0 dollars
            pick.points = 0

            weekly_earnings = get_earnings(pick.alternate)

            # Multiply by the pick point multiplier -- defines if a rule was used.
            weekly_earnings = pick.point_multiplier * weekly_earnings
            # We need to add the alternate as the main pick.
            updated_pick = Pick(
                event=pick.event,
                pick=pick.alternate,
                alternate=pick.alternate,
                name=pick.name,
                points=weekly_earnings,
                season=pick.season,
            )
            db.session.add(updated_pick)
        else:
            # Get the earnings
            weekly_earnings = get_earnings(player_name)
            weekly_earnings = pick.point_multiplier * weekly_earnings

            # Update the pick with this value
            pick.points = weekly_earnings

        # Commit the changes
        db.session.commit()
