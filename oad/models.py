from datetime import datetime

from flask_login import UserMixin
from sqlalchemy.inspection import inspect

from . import db


class Serializer(object):
    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(lst):
        return [item.serialize() for item in lst]


class User(UserMixin, db.Model, Serializer):
    __table_args__ = {"extend_existing": True}
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000), unique=True)
    picks = db.relationship("Pick", backref="user", lazy=True)
    strikes_remaining = db.Column(db.Integer, default=1)  # breakfast_ball
    is_admin = db.Column(db.Boolean, default=False)
    email_confirmed = db.Column(db.Boolean, default=False)
    display_name = db.Column(db.Text, default="")
    strike_event = db.Column(db.Text, default="")
    substitute_event = db.Column(db.Text, default="")
    double_up_event = db.Column(db.Text, default="")
    liv_line_event = db.Column(db.Text, default="")
    substitutes_remaining = db.Column(db.Integer, default=1)  # tap_in
    double_up_remaining = db.Column(db.Integer, default=1)  # double_up
    liv_line_remaining = db.Column(db.Integer, default=1)  # liv_line


class Pick(db.Model, Serializer):
    __table_args__ = {"extend_existing": True}
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String(1000), index=True)
    pick = db.Column(db.String(1000))
    alternate = db.Column(db.String(1000))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    name = db.Column(db.String(1000), db.ForeignKey("user.name"), nullable=False)
    points = db.Column(db.Float(), default=-1e-9)
    season = db.Column(db.Integer)
    point_multiplier = db.Column(db.Integer, default=1)
    fedex = db.Column(db.Float(), default=-1e-9)

    def serialize(self):
        d = Serializer.serialize(self)
        return d


class Player(db.Model, Serializer):
    __table_args__ = {"extend_existing": True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000), unique=True)
    cumulative_points = db.Column(db.Float())
