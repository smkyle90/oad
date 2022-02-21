"""Admin actions.
"""

from .. import db
from ..models import Pick, Player
from . import get_earnings, get_fedex_points, get_withdrawl_list


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
        player_fedex = get_fedex_points(player_name)

        if player_name in withdrawl_list:
            print(f"{player_name} withdrawn")
            # They have withdrawn and thus earn 0 dollars
            pick.points = 0
            pick.fedex = 0

            weekly_earnings = get_earnings(pick.alternate)
            weekly_fedex = get_fedex_points(pick.alternate)

            # Multiply by the pick point multiplier -- defines if a rule was used.
            weekly_earnings = pick.point_multiplier * weekly_earnings
            weekly_fedex = pick.point_multiplier * weekly_fedex

            # Add a new pick, so the primary and secondary golfer are used
            # We need to add the alternate as the main pick.
            updated_pick = Pick(
                event=pick.event,
                pick=pick.alternate,
                alternate=pick.alternate,
                name=pick.name,
                points=weekly_earnings,
                season=pick.season,
                fedex=weekly_fedex,
            )
            db.session.add(updated_pick)
        elif player_fedex == -1:
            print(f"{player_name} did not start")

            # Multiply by the pick point multiplier -- defines if a rule was used.
            weekly_earnings = get_earnings(pick.alternate)
            weekly_earnings = pick.point_multiplier * weekly_earnings

            weekly_fedex = get_fedex_points(pick.alternate)
            weekly_fedex = pick.point_multiplier * weekly_fedex

            # Modify the pick, as the primary golder did not tee off
            pick.pick = pick.alternate
            pick.points = weekly_earnings
            pick.fedex = weekly_fedex
        else:
            # Get the earnings
            weekly_earnings = get_earnings(player_name)
            weekly_earnings = pick.point_multiplier * weekly_earnings

            weekly_fedex = get_fedex_points(player_name)
            weekly_fedex = pick.point_multiplier * weekly_fedex

            # Update the pick with this value
            pick.points = weekly_earnings
            pick.fedex = weekly_fedex

        # Commit the changes
        db.session.commit()
