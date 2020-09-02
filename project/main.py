from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from . import db
from .helpers import get_earnings, get_event, get_picks
from .models import Pick, Player, User
from .views import PickTable, PlayerTable, UserTable

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/profile")
@login_required
def profile():
    return render_template("profile.html", user=current_user)


@main.route("/leaders")
@login_required
def leaders():
    users = User.query.all()
    user_table = UserTable(users)

    picks = Pick.query.all()
    pick_table = PickTable(picks)

    players = Player.query.all()
    player_table = PlayerTable(players)

    return render_template(
        "leaders.html", u_table=user_table, p_table=pick_table, pl_table=player_table
    )


@main.route("/pick")
@login_required
def pick():
    # Get pick history for current user
    # Available picks
    avail_picks = get_picks()

    # Get current event
    curr_event = get_event()

    return render_template(
        "pick.html", avail=avail_picks, event=curr_event, user=current_user.name
    )


@main.route("/submit_pick", methods=["POST"])
@login_required
def submit_pick():
    # Get current event
    curr_event = "Test Open"
    selection = request.form.get("Select")

    # Get the list of Players in the DB.
    curr_players = Player.query.all()

    # If player does not exist, we need to add them to the player table
    if selection not in [player.name for player in curr_players]:
        earnings = get_earnings()
        new_player = Player(name=selection, cumulative_points=earnings)
        db.session.add(new_player)
        db.session.commit()

    # See if pick has been made
    prev_pick = (
        Pick.query.filter_by(event=curr_event).filter_by(name=current_user.name).first()
    )

    if prev_pick is None:
        user_pick = Pick(event=curr_event, pick=selection, name=current_user.name)
        db.session.add(user_pick)
    else:
        prev_pick.pick = selection

    # The user is able to make a pick
    db.session.commit()

    return redirect(url_for("main.profile"))
