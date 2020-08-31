from datetime import datetime 
from flask_login import UserMixin
from . import db

class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000), unique=True)
    picks = db.relationship('Pick', backref='user', lazy=True)

class Pick(db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    event = db.Column(db.String(1000))
    pick = db.Column(db.String(1000))
    # timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    name = db.Column(db.Integer, db.ForeignKey('user.name'))

    # def __repr__(self):
    #     return "{} picks {}".format(self.name, self.pick)

# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(64), index=True, unique=True)
#     email = db.Column(db.String(120), index=True, unique=True)
#     password_hash = db.Column(db.String(128))
#     posts = db.relationship('Post', backref='author', lazy='dynamic')

#     def __repr__(self):
#         return '<User {}>'.format(self.username)

# class Post(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     body = db.Column(db.String(140))
#     timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

#     def __repr__(self):
#         return '<Post {}>'.format(self.body)

# def init_db():
#     db.create_all()

# if __name__ == '__main__':
#     init_db()