import datetime
import json
import os

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .models import Pick, Player, User
from .util import (
    check_rule_status,
    construct_user_table,
    create_pick_table,
    format_earnings,
    get_earnings,
    get_event_info,
    get_weekly_pick_table,
    major_draft_pool,
    send_email,
    update_cache_from_api,
    update_weekly_pick_table,
)
from .util.admin import add_user_points
from .views import league_page

SEASON = int(os.getenv("OADYR", 2022))

EMPTY_HTML = "<div></div>"

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
    update_cache_from_api()

    curr_event, __, tournament_state, event_table, __ = get_event_info()

    users = User.query.all()
    all_picks = Pick.query.filter_by(season=SEASON).all()
    user_table = construct_user_table(users, all_picks, as_html=False)

    week_picks = Pick.query.filter_by(season=SEASON).filter_by(event=curr_event).all()

    update_weekly_pick_table(users, week_picks, event_table, user_table)

    # Determine if we are going to show the picks for the week
    if tournament_state in ["in", "post"]:
        show_picks = True
        pick_table = get_weekly_pick_table()
        if pick_table is None:
            pick_table = EMPTY_HTML
    else:
        show_picks = False
        week_picks = []
        pick_table = EMPTY_HTML

    if tournament_state != "in":
        show_historical_data = True
        pick_history_table, bar, line = league_page(users, SEASON)
    else:
        show_historical_data = False
        pick_history_table, bar, line = EMPTY_HTML, EMPTY_HTML, EMPTY_HTML

    if event_table is None:
        event_table = EMPTY_HTML
    else:
        event_table = event_table.to_html(
            classes="data", border=0, index=False, header=False
        )

    return render_template(
        "league.html",
        u_table=user_table.to_html(classes="data", border=0, index=False),
        p_table=pick_table,
        ph_table=pick_history_table,
        show_picks=show_picks,
        show_data=show_historical_data,
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
    curr_event, avail_picks, tournament_state, __, tournament_round = get_event_info()

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
    try:
        eligible_picks = [p for p in avail_picks if p not in all_players]
    except Exception:
        eligible_picks = []

    strike_used, tap_in_used, double_up_used = check_rule_status(
        current_user, curr_event
    )

    strike_button_state = False
    substitute_button_state = False
    double_up_button_state = False
    button_text = ""

    if eligible_picks:
        eligible_picks.sort()

        # Warn the user about the picking state
        if tournament_round < 1:
            if prev_pick is None:
                pick_state = "you have yet to pick. Pick any golfer in the field."
            else:
                pick_state = "you have already picked, but can modify your pick free of charge. Pick any other golfer in the field."

            strike_button_state = True
            button_text = "Submit Pick"

        elif tournament_round <= 2:
            # Allow user to use strike
            if not strike_used:
                if prev_pick is None:
                    pick_state = "the tourney has started and you have not picked, but you have a Breakfast Ball. Picking now will use this up. Prior to the start of Round 2, you can pick a player who has yet to tee off."
                    button_text = "Pick and Use Breakfast Ball"
                else:
                    pick_state = "the tourney has started and you've made a pick, but you have a Breakfast Ball. Picking now will use this up. Prior to the start of Round 2, you can pick a player who has yet to tee off."
                    button_text = "Re-pick and Use Breakfast Ball"

                strike_button_state = True
                button_text = "Use Breakfast Ball"

            else:
                pick_state = "the tourney has started and you have either made your pick, Round 2 has started, or don't have a Breakfast Ball."
        else:
            pick_state = "you are out of options for this week."
    else:
        if tournament_round < 1:
            pick_state = (
                "our friends at ESPN have not released the field for this week."
            )
        else:
            pick_state = "no players left to pick from."

    # Allow user to substitue their alternate in
    if (prev_pick) and (not tap_in_used) and (1 <= tournament_round < 3):
        substitute_button_state = True

    # Allow user the double up their earnings for the week
    if (prev_pick) and (not double_up_used) and (1 <= tournament_round < 4):
        double_up_button_state = True

    if tournament_round:
        tournament_round = str(tournament_round)
    else:
        tournament_round = "Pre-tournament"

    if prev_pick is None:
        prev_pick_show = ""
        prev_alt_show = ""
    else:
        prev_pick_show = (prev_pick.pick,)
        prev_alt_show = prev_pick.alternate

    return render_template(
        "pick.html",
        avail=eligible_picks,
        event=curr_event,
        user=current_user.name,
        pick_text=pick_state,
        strike_button_state=strike_button_state,
        submit_text=button_text,
        substitute_button_state=substitute_button_state,
        double_up_button_state=double_up_button_state,
        current_round=tournament_round,
        prev_pick_show=prev_pick_show,
        prev_alt_show=prev_alt_show,
    )


@main.route("/submit_pick", methods=["POST"])
@login_required
def submit_pick():
    # Get current event from the session
    curr_event, __, tournament_state, __, tournament_round = get_event_info()

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
    if tournament_round < 1:
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

    elif (tournament_round <= 2) and (current_user.strikes_remaining):
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
        current_user.strike_event = curr_event

    # The user is able to make a pick
    db.session.commit()

    return redirect(url_for("main.profile"))


@main.route("/update")
@login_required
def update():
    __, __, tournament_state, __, __ = get_event_info()

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


@main.route("/confirm_tap_in", methods=["POST"])
@login_required
def confirm_tap_in():
    curr_event, _, _, _, _ = get_event_info()

    # See if pick has been made
    prev_pick = (
        Pick.query.filter_by(season=SEASON)
        .filter_by(event=curr_event)
        .filter_by(name=current_user.name)
        .first()
    )

    prev_pick.point_multiplier = 0

    new_pick = Pick(
        event=curr_event,
        pick=prev_pick.alternate,
        alternate=prev_pick.alternate,
        name=current_user.name,
        season=SEASON,
    )

    current_user.substitute_event = curr_event
    current_user.substitutes_remaining = 0

    db.session.add(new_pick)
    db.session.commit()

    return redirect(url_for("main.profile"))


@main.route("/confirm_double_up", methods=["POST"])
@login_required
def confirm_double_up():
    curr_event, _, _, _, _ = get_event_info()

    # See if pick has been made
    curr_pick = (
        Pick.query.filter_by(season=SEASON)
        .filter_by(event=curr_event)
        .filter_by(name=current_user.name)
        .first()
    )

    curr_pick.point_multiplier = 2
    current_user.double_up_event = curr_event
    current_user.double_up_remaining = 0
    db.session.commit()

    return redirect(url_for("main.profile"))


@main.route("/use_tap_in")
@login_required
def use_tap_in():
    return render_template("tap_in.html")


@main.route("/use_double_up")
@login_required
def use_double_up():
    return render_template("double_up.html")


@main.route("/user_display_name_change", methods=["POST"])
@login_required
def user_display_name_change():

    new_name = request.form.get("new_name")

    user = User.query.filter_by(email=current_user.email).first()

    user.display_name = new_name

    db.session.commit()

    return render_template("update_display_name.html", team_name=new_name)


@main.route("/update_display_name")
@login_required
def update_display_name():

    user = User.query.filter_by(email=current_user.email).first()

    team_name = user.display_name

    if not team_name:
        team_name = user.name

    return render_template("update_display_name.html", team_name=team_name)


@main.route("/weekly_update", methods=["POST"])
@login_required
def weekly_update():
    curr_event, __, __, __, __ = get_event_info()

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


def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()


@main.route("/api/picks/")
@login_required
def get_all_picks():
    picks = Pick.query.filter_by(season=SEASON).all()
    picks = [pick for pick in picks if pick.points >= 0]
    return json.dumps(Pick.serialize_list(picks), default=myconverter)


@main.route("/api/picks/<name>/")
@login_required
def get_player_picks(name):
    picks = Pick.query.filter_by(season=SEASON).filter_by(name=name).all()
    picks = [pick for pick in picks if pick.points >= 0]
    return json.dumps(Pick.serialize_list(picks), default=myconverter)


@main.route("/mdp")
@login_required
def mdp():
    # __, __, tournament_state, __, __ = get_event_info()

    # update_button = False

    # if tournament_state == "post":
    #     update_button = True

    agg_df, score_df = major_draft_pool()

    agg_df = agg_df.to_html(classes="data", border=0, index=True, header=True)

    score_df = score_df.to_html(classes="data", border=0, index=True, header=True)

    return render_template("mdp.html", u_table=agg_df, s_table=score_df)
