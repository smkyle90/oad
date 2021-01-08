from datetime import datetime

from flask_login import UserMixin

from . import db


class User(UserMixin, db.Model):
    __table_args__ = {"extend_existing": True}
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000), unique=True)
    picks = db.relationship("Pick", backref="user", lazy=True)
    strikes_remaining = db.Column(db.Integer, default=1)
    is_admin = db.Column(db.Boolean, default=False)
    email_confirmed = db.Column(db.Boolean, default=False)


class Pick(db.Model):
    __table_args__ = {"extend_existing": True}
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String(1000), index=True)
    pick = db.Column(db.String(1000))
    alternate = db.Column(db.String(1000))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    name = db.Column(db.String(1000), db.ForeignKey("user.name"), nullable=False)
    points = db.Column(db.Float(), default=-1e-9)
    season = db.Column(db.Integer)


class Player(db.Model):
    __table_args__ = {"extend_existing": True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000), unique=True)
    cumulative_points = db.Column(db.Float())
