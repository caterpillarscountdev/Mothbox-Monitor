import os
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

connection_string = os.environ.get("DATABASE_URI", "sqlite:///db.sqlite")
if os.environ.get("DATABASE_USER"):
    USER = os.environ.get("DATABASE_USER")
    PASS = os.environ.get("DATABASE_PASSWORD")
    HOST = os.environ.get("DEVCCDB_SERVICE_HOST")
    DB = os.environ.get("DATABASE_NAME")
    connection_string = f"mysql+mysqldb://{USER}:{PASS}@{HOST}/{DB}"
    

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_`%(constraint_name)s`",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
    }

class ModelBase(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)

db = SQLAlchemy(model_class=ModelBase)

migrate = Migrate()

def init_app(app):
    db.init_app(app)
    migrate.init_app(app, db)
