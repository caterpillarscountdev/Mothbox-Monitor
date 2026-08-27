import os

from datetime import timezone

from flask import Flask, redirect, url_for
from flask_mail import Mail
from flask_security import current_user
from flask_rq import RQ
import rq_dashboard

from . import database, auth, jobs

@rq_dashboard.blueprint.before_request
def restrict_to_admins():
    if current_user.is_anonymous or not current_user.can("admin"):
        return redirect(url_for('main.index'))


def create_app(testing=False, redis_connection=None):
    app = Flask(__name__)
    #app.config["EXPLAIN_TEMPLATE_LOADING"] = True
    app.config["SECRET_KEY"] = os.environ.get("APP_SECRET_KEY", 'notverysecretindev')
    app.config["SQLALCHEMY_DATABASE_URI"] = database.connection_string
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config["SQLALCHEMY_ECHO"] = os.environ.get("SQL_ECHO", False)
    
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
    app.testing = testing

    os_redis = os.environ.get('REDIS_SERVICE_HOST', None)
    if redis_connection:
        app.config["RQ_CONNECTION"] = redis_connection
    elif os_redis:
        os_redis_port = os.environ.get("REDIS_SERVICE_PORT", "6379")
        os_redis_password = os.environ.get("REDIS_PASSWORD", "")
        app.config["RQ_CONNECTION"] = f'redis://:{os_redis_password}@{os_redis}:{os_redis_port}/0'
    print("RQ_CONNECTION", app.config["RQ_CONNECTION"])
        
        
    mail = Mail(app)
    database.init_app(app)
    auth.init_app(app)
    jobs.init_app(app)

    
    app.config["RQ_DASHBOARD_REDIS_URL"] = app.config.get("RQ_CONNECTION", "redis:///")
    rq_dashboard.web.setup_rq_connection(app)
    app.register_blueprint(rq_dashboard.blueprint, url_prefix="/_rq")
    
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
