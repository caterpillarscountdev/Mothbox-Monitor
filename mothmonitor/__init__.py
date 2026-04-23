import os

from datetime import timezone

from flask import Flask
from flask_mail import Mail

from . import database, auth

def create_app(testing=False):
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

    app.config["SECURITY_EMAIL_SUBJECT_PASSWORD_RESET"] = "Set your new password"
    app.config["SECURITY_EMAIL_PLAINTEXT"] = False
    
    app.config["TESTING"] = testing
    
    mail = Mail(app)
    database.init_app(app)
    auth.init_app(app)


    from .blueprints import main, users, upload, devices, datasets
    
    app.register_blueprint(main.main)
    app.register_blueprint(users.users, url_prefix="/users")
    app.register_blueprint(upload.upload, url_prefix="/upload")
    app.register_blueprint(devices.devices, url_prefix="/devices")
    app.register_blueprint(datasets.datasets, url_prefix="/datasets")

    @app.template_filter()
    def format_datetime(value, format='date', utc=True):
        if not value:
            return ""
        if utc:
            value = value.replace(tzinfo=timezone.utc).astimezone(tz=None)
        if format == 'date':
            format="%b %d, %Y"
        elif format == 'datetime':
            format="%b %d, %Y %I:%M %p"
        return value.strftime(format)
    
    return app
