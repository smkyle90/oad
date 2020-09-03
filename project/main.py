from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from . import db
from .helpers import construct_user_table, get_earnings, get_event_info
from .models import Pick, Player, User
from .scheduled import add_user_points
from .views import PickTable, PlayerTable, UserPickTable, UserTable

main = Blueprint("main", __name__)


def set_state():
    """Set the session variables.
    """
    event_name, __, tournament_state = get_event_info()

    if "event_state" not in session:
        session["event_state"] = tournament_state
    if "event_name" not in session:
        session["name"] = event_name


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/profile")
@login_required
def profile():
    picks = Pick.query.filter_by(name=current_user.name).all()
    pick_table = UserPickTable(picks)
    total_points = sum([int(x.points) for x in picks])
    # total_points = 1
    return render_template(
        "profile.html",
        user=current_user,
        pick_table=pick_table,
        user_points=total_points,
    )


@main.route("/league")
@login_required
def league():
    add_user_points()
    users = User.query.all()

    picks = Pick.query.filter_by(event=session["event_name"]).all()
    pick_table = PickTable(picks)

    players = Player.query.all()
    player_table = PlayerTable(players)

    user_table = construct_user_table(users, picks)

    # Determine if we are going to show the picks for the week
    if session["event_state"] != "pre":
        show_picks = True
    else:
        show_picks = True

    return render_template(
        "league.html",
        u_table=user_table,
        p_table=pick_table,
        pl_table=player_table,
        show_picks=show_picks,
    )


@main.route("/pick")
@login_required
def pick():
    # Get pick history for current user
    # Available picks
    # avail_picks = get_picks()
    # # Get current event
    # curr_event = get_event()

    curr_event, avail_picks, tournament_state = get_event_info()

    if "event_name" not in session:
        session["event_name"] = curr_event
    if "event_state" not in session:
        session["event_state"] = tournament_state

    # Check if the user has made a previous pick
    prev_pick = (
        Pick.query.filter_by(event=curr_event).filter_by(name=current_user.name).first()
    )

    button_state = True
    button_text = "Submit Pick"
    # Warn the user about the picking state
    if session["event_state"] == "pre":
        if prev_pick is None:
            pick_state = "you have yet to pick."
        else:
            pick_state = (
                "you have already picked, but can modify your pick free of charge."
            )
    else:
        if (prev_pick is None) and (current_user.strikes_remaining):
            pick_state = "the tourney has started and you have not picked, but you have a strike. Picking now will use this up."
            button_text = "Pick and Use Strike"
        else:
            pick_state = "mate, the tourney has started and you have either made your pick, or don't have any strikes left."
            button_state = False

    return render_template(
        "pick.html",
        avail=avail_picks,
        event=curr_event,
        user=current_user.name,
        pick_text=pick_state,
        button=button_state,
        submit_text=button_text,
    )


@main.route("/submit_pick", methods=["POST"])
@login_required
def submit_pick():
    # Get current event from the session
    curr_event = session["event_name"]

    # Get the selection
    selection = request.form.get("Select")

    # Get the list of Players in the DB.
    curr_players = Player.query.all()

    # If player does not exist, we need to add them to the player table
    if selection not in [player.name for player in curr_players]:
        earnings = get_earnings(selection)
        new_player = Player(name=selection, cumulative_points=earnings)
        db.session.add(new_player)
        db.session.commit()

    # See if pick has been made
    prev_pick = (
        Pick.query.filter_by(event=curr_event).filter_by(name=current_user.name).first()
    )

    # Ensure a player does not pick before the tournament has started.
    # If they do not pick before it starts, and have a strike, they can make
    # a pick and use it.
    if session["event_state"] == "pre":
        if prev_pick is None:
            user_pick = Pick(event=curr_event, pick=selection, name=current_user.name)
            db.session.add(user_pick)
        else:
            prev_pick.pick = selection
    else:
        if (prev_pick is None) and (current_user.strikes_remaining):
            user_pick = Pick(event=curr_event, pick=selection, name=current_user.name)
            db.session.add(user_pick)

            # Need to issue a strike to user.
            current_user.strikes_remaining = 0

        else:
            print("Already made pick. Cannot change pick once tournament has begun.")

    # The user is able to make a pick
    db.session.commit()

    return redirect(url_for("main.profile"))
