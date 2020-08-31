from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import User, Pick
from .views import UserTable, PickTable

from . import db

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@main.route('/leaders')
@login_required
def leaders():
    users = User.query.all()
    user_table = UserTable(users)

    picks = Pick.query.all()
    pick_table = PickTable(picks)

    return render_template('leaders.html', u_table=user_table, p_table=pick_table)

@main.route('/pick')
@login_required
def pick():
    current_user
    # Get pick history for current user

    # Available picks
    avail_picks = ['TW', 'PM', 'DJ', 'AS']

    # Get current event
    curr_event = "Test Open"
    return render_template('pick.html', avail=avail_picks, event=curr_event)

@main.route("/submit_pick" , methods=['POST'])
@login_required
def submit_pick():
    # Get current event
    curr_event = "Test Open"
    selection = request.form.get('Select')

    user_pick = Pick(event=curr_event, pick=selection)
    db.session.add(user_pick)
    db.session.commit()

    flash('Pick made')
    return redirect(url_for('main.profile'))