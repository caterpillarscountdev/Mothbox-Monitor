import os
from flask_security import Security, SQLAlchemyUserDatastore

from .models import db, User, Role

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(datastore=user_datastore)

def init_app(app):
    app.config['SECURITY_PASSWORD_SALT'] = os.environ.get("SECURITY_PASSWORD_SALT", '146585145368132386173505678016728509634')
    app.config['SECURITY_CHANGEABLE'] = True
    app.config['SECURITY_CHANGE_EMAIL'] = True
    
    app.config['SECURITY_URL_PREFIX'] = '/auth'

    security.init_app(app)
