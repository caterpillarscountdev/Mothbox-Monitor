from flask_security.models import fsqla_v3 as fsqla
from .database import db

fsqla.FsModels.set_db_info(db)

class User(db.Model, fsqla.FsUserMixin):
    email = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(32), index=True)

class Role(db.Model, fsqla.FsRoleMixin):
    pass
