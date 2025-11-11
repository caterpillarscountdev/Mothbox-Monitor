import os

from flask import Flask

from . import database, auth

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("APP_SECRET_KEY", 'notverysecretindev')
    app.config["SQLALCHEMY_DATABASE_URI"] = database.connection_string
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    database.init_app(app)
    auth.init_app(app)


    from .blueprints.auth import auth as auth_blueprint
    from .blueprints.main import main as main_blueprint

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(main_blueprint)

    return app
