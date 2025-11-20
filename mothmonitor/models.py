from typing import List
import datetime
import secrets

from sqlalchemy import ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship


from flask_security.models import fsqla_v3 as fsqla

from .database import db

fsqla.FsModels.set_db_info(db)

class User(db.Model, fsqla.FsUserMixin):
    name: Mapped[str] = mapped_column(index=True, nullable=True)

class Role(db.Model, fsqla.FsRoleMixin):
    pass



class Device(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True, nullable=True)
    upload_key: Mapped[str] = mapped_column(index=True, nullable=True,
                                            default=lambda: secrets.token_hex(16))
    last_seen: Mapped[datetime.datetime] = mapped_column(nullable=True)

