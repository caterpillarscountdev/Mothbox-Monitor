from flask_security import Security, SQLAlchemyUserDatastore

from .models import db, User, Role

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(datastore=user_datastore)

def init_app(app):
    security.init_app(app)
