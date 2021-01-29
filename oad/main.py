import os

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .models import Pick, Player, User
from .scheduled import set_state
from .util import (
    construct_user_table,
    create_pick_table,
    format_earnings,
    get_earnings,
    get_event_info,
    send_email,
)
from .util.admin import add_user_points

from .views import (  # create_plot,; pick_matrix,
    PickTable,
    # PlayerTable,
    # UserPickTable,
    # UserTable,
    league_page,
    # live_scores,
    weekly_pick_table,
)

SEASON = int(os.getenv("OADYR", 2021))

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/rules")
@login_required
def rules():
    return render_template("rules.html")


@main.route("/profile")
@login_required
def profile():
    picks = Pick.query.filter_by(season=SEASON).filter_by(name=current_user.name).all()
    # pick_table = UserfPickTable(picks)

    pick_table = create_pick_table(picks)

    total_points = format_earnings(sum([int(x.points) for x in picks]))
    # total_points = 1
    return render_template(
        "profile.html",
        user=current_user,
        pick_table=pick_table,
        user_points=total_points,
        season=SEASON,
    )


@main.route("/league")
@login_required
def league():
    curr_event, __, tournament_state, event_table = get_event_info()

    users = User.query.all()

    week_picks = Pick.query.filter_by(season=SEASON).filter_by(event=curr_event).all()

    # try:
    #     pick_table = live_scores(week_picks)
    # except Exception:
    # pick_table = PickTable(week_picks)

    pick_table = weekly_pick_table(users, week_picks)

    all_picks = Pick.query.filter_by(season=SEASON).all()
    user_table = construct_user_table(users, all_picks)

    pick_history_table, bar, line = league_page(users, SEASON)

    # Determine if we are going to show the picks for the week
    if tournament_state in ["in", "post"]:
        show_picks = True
    else:
        show_picks = False

    return render_template(
        "league.html",
        u_table=user_table,
        p_table=pick_table,
        ph_table=pick_history_table,
        show_picks=show_picks,
        event_name=curr_event,
        event_table=event_table,
        plot=bar,
        points=line,
        season=SEASON,
        # bp_table=best_picks,
    )


@main.route("/pick")
@login_required
def pick():
    curr_event, avail_picks, tournament_state, __ = get_event_info()

    # Check if the user has made a previous pick for this event
    prev_pick = (
        Pick.query.filter_by(season=SEASON)
        .filter_by(event=curr_event)
        .filter_by(name=current_user.name)
        .first()
    )

    # Get all picks for this user
    all_picks = (
        Pick.query.filter_by(season=SEASON).filter_by(name=current_user.name).all()
    )

    # Get the list of players already picked
    all_players = [pick.pick for pick in all_picks]

    # We can pick from the available picks, minus the players we've already picked.
    # TODO: set operations?
    eligible_picks = [p for p in avail_picks if p not in all_players]

    button_state = True
    button_text = "Submit Pick"

    if eligible_picks:
        eligible_picks.sort()

        # Warn the user about the picking state
        if tournament_state == "pre":
            if prev_pick is None:
                pick_state = "you have yet to pick. Pick any golfer in the field."
            else:
                pick_state = "you have already picked, but can modify your pick free of charge. Pick any other golfer in the field."
        else:
            if (prev_pick is None) and (current_user.strikes_remaining):
                pick_state = "the tourney has started and you have not picked, but you have a strike. Picking now will use this up. You can pick a player who has yet to tee off."
                button_text = "Pick and Use Strike"
            else:
                pick_state = "mate, the tourney has started and you have either made your pick, or don't have any strikes left... better luck next week."
                button_state = False
    else:
        if tournament_state == "pre":
            pick_state = (
                "our friends at ESPN have not released the field for this week."
            )
        else:
            pick_state = "no players left to pick from."

        button_state = False

    return render_template(
        "pick.html",
        avail=eligible_picks,
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
    curr_event, __, tournament_state, __ = get_event_info()

    # Get the selection
    selection = request.form.get("main")
    alternate = request.form.get("alternate")

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
        Pick.query.filter_by(season=SEASON)
        .filter_by(event=curr_event)
        .filter_by(name=current_user.name)
        .first()
    )

    # Ensure a player does not pick before the tournament has started.
    # If they do not pick before it starts, and have a strike, they can make
    # a pick and use it.
    if tournament_state == "pre":
        if prev_pick is None:
            user_pick = Pick(
                event=curr_event,
                pick=selection,
                alternate=alternate,
                name=current_user.name,
                season=SEASON,
            )
            db.session.add(user_pick)
        else:
            prev_pick.pick = selection
            prev_pick.alternate = alternate
    else:
        if (prev_pick is None) and (current_user.strikes_remaining):
            user_pick = Pick(
                event=curr_event,
                pick=selection,
                alternate=alternate,
                name=current_user.name,
                season=SEASON,
            )
            db.session.add(user_pick)

            # Need to issue a strike to user.
            current_user.strikes_remaining = 0

        else:
            print("Already made pick. Cannot change pick once tournament has begun.")

    # The user is able to make a pick
    db.session.commit()

    return redirect(url_for("main.profile"))


@main.route("/update")
@login_required
def update():
    __, __, tournament_state, __ = get_event_info()

    update_button = False

    if tournament_state == "post":
        update_button = True

    return render_template("update.html", update_button=update_button)


@main.route("/end_week")
@login_required
def end_week():
    add_user_points()
    # update_player_earnings()
    flash("Update complete!")
    return redirect(url_for("main.update"))


@main.route("/user_password_change", methods=["POST"])
@login_required
def user_password_change():
    old_pass = request.form.get("old_pw")
    new_pass1 = request.form.get("pw1")
    new_pass2 = request.form.get("pw2")

    user = User.query.filter_by(email=current_user.email).first()

    if check_password_hash(user.password, old_pass):
        if new_pass1 == new_pass2:
            user.password = generate_password_hash(new_pass1, method="sha256")
            # db.session.add(user)
            db.session.commit()
            flash("Password has been updated.", "success")
            return redirect(url_for("main.profile"))
        else:
            flash("The new password entries do not match.")
    else:
        flash("The old password is incorrect.")

    return render_template("update_password.html")


@main.route("/update_password")
@login_required
def update_password():
    return render_template("update_password.html")


@main.route("/user_display_name_change", methods=["POST"])
@login_required
def user_display_name_change():

    new_name = request.form.get("new_name")

    user = User.query.filter_by(email=current_user.email).first()

    user.display_name = new_name

    db.session.commit()
    print("new name", new_name)
    return render_template("update_display_name.html", team_name=new_name)


@main.route("/update_display_name")
@login_required
def update_display_name():

    user = User.query.filter_by(email=current_user.email).first()

    team_name = user.display_name

    print("team name", team_name)
    if not team_name:
        team_name = user.name
    print("team name", team_name)

    return render_template("update_display_name.html", team_name=team_name)


@main.route("/weekly_update", methods=["POST"])
@login_required
def weekly_update():
    curr_event, __, __, __ = get_event_info()

    users = User.query.all()
    picks = Pick.query.filter_by(season=SEASON).all()

    written_text = request.form.get("Email")
    points_table = construct_user_table(users, picks, curr_event)

    email_text = "<p>{}</p>\n\n{}".format(written_text, points_table)

    for user_addr in [user.email for user in users]:
        try:
            send_email(user_addr, "Weekly Update - {}".format(curr_event), email_text)
        except Exception as e:
            flash("Unable to send email to users. Message: {}".format(e))
    flash("Messages sent!")
    return redirect(url_for("main.update"))
