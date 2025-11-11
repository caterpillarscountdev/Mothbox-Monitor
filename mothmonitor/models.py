from flask_login import UserMixin
from .database import db

class User(db.Model, UserMixin):
    email = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(32), index=True)
