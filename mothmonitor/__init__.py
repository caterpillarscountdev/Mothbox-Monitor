import os

from flask import Flask
from flask_mail import Mail

from . import database, auth

def create_app():
    app = Flask(__name__)
    #app.config["EXPLAIN_TEMPLATE_LOADING"] = True
    app.config["SECRET_KEY"] = os.environ.get("APP_SECRET_KEY", 'notverysecretindev')
    app.config["SQLALCHEMY_DATABASE_URI"] = database.connection_string
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    app.config["REMEMBER_COOKIE_SAMESITE"] = "strict"
    app.config["SESSION_COOKIE_SAMESITE"] = "strict"

    app.config["S3_BUCKET"] = os.environ.get("S3_BUCKET", "")
    # Also expects AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in environ
    #
    app.config["MAIL_SERVER"] = os.environ.get("MAIL_SERVER", "relay.unc.edu")
    app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER", 'lopp+mothmonitor@unc.edu')

    mail = Mail(app)
    database.init_app(app)
    auth.init_app(app)


    from .blueprints import main, users, upload, devices
    
    app.register_blueprint(main.main)
    app.register_blueprint(users.users, url_prefix="/users")
    app.register_blueprint(upload.upload, url_prefix="/upload")
    app.register_blueprint(devices.devices)

    return app
