"""Scheduled Tasks each week.
"""
from flask import session, Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
import pandas as pd

from . import db
from .helpers import get_earnings, get_event, get_picks, get_event_info, construct_user_table
from .models import Pick, Player, User
from .views import PickTable, PlayerTable, UserTable, UserPickTable


def send_pick_reminder():
	pass

def send_picks():
	"""Send the picks for the week.
	"""
	pass

def send_weekly_update():
	"""Send a weekly summary.
	"""
	pass

def update_player_earnings():
	"""Update the player earnings in the player DB with their 
	updated TOTAL MONEY (or MONEY)
	"""

	all_players = Players.query.all()

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
		new_earnings = get_earnings(player_name)

		# Get the old earnings
		player = Player.query.filter_by(name=player_name).first()
		old_earnings = player.cumulative_points

		print (type(old_earnings))
		print (type(new_earnings))
		# This is what the player earned this week.
		delta_earnings = new_earnings - old_earnings

		# Update the pick with this value
		pick.points = delta_earnings

		# Commit the changes
		db.session.commit()



