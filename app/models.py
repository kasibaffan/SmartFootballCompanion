from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120))
    age = db.Column(db.Integer)
    position = db.Column(db.String(80))
    level = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)

    stats = db.relationship(
        "StatEntry", backref="user", lazy=True, order_by="StatEntry.timestamp"
    )
    live_matches = db.relationship(
        "Match", backref="user", lazy=True, order_by="Match.started_at"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class StatEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    matches = db.Column(db.Integer)
    distance = db.Column(db.Float)
    minutes = db.Column(db.Integer)
    challenges = db.Column(db.Integer)
    goals = db.Column(db.Integer)
    assists = db.Column(db.Integer)
    injuries = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    opponent = db.Column(db.String(120))
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)

    events = db.relationship(
        "MatchEvent", backref="match", lazy=True, order_by="MatchEvent.created_at"
    )

    @property
    def is_active(self):
        return self.ended_at is None


class MatchEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("match.id"), nullable=False)
    event_type = db.Column(db.String(20), nullable=False)  # goal / card / sub / note
    minute = db.Column(db.Integer)
    note = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
