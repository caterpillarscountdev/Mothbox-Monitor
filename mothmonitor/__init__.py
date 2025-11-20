import os

from flask import Flask

from . import database, auth

def create_app():
    app = Flask(__name__)
    #app.config["EXPLAIN_TEMPLATE_LOADING"] = True
    app.config["SECRET_KEY"] = os.environ.get("APP_SECRET_KEY", 'notverysecretindev')
    app.config["SQLALCHEMY_DATABASE_URI"] = database.connection_string
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    app.config['SECURITY_PASSWORD_SALT'] = os.environ.get("SECURITY_PASSWORD_SALT", '146585145368132386173505678016728509634')
    app.config["REMEMBER_COOKIE_SAMESITE"] = "strict"
    app.config["SESSION_COOKIE_SAMESITE"] = "strict"

    database.init_app(app)
    auth.init_app(app)


    from .blueprints import main, upload
    
    app.register_blueprint(main.main)
    app.register_blueprint(upload.upload)

    return app
