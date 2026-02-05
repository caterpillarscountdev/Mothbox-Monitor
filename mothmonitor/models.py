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

    def can(self, perm):
        for role in self.roles:
            if perm in role.permissions:
                return True
        return False

class Role(db.Model, fsqla.FsRoleMixin):
    pass



class Night(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    night: Mapped[datetime.date] = mapped_column(index=True, nullable=True)
    uploaded_started_at: Mapped[datetime.datetime] = mapped_column(nullable=True)
    photo_count: Mapped[int] = mapped_column(nullable=True)
    
    device_id: Mapped[int] = mapped_column(ForeignKey("device.id"))
    device: Mapped["Device"] = relationship(back_populates="nights")    


class Device(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(index=True, nullable=True)
    label: Mapped[str] = mapped_column(nullable=True)
    upload_key: Mapped[str] = mapped_column(index=True, nullable=True)
    former_keys: Mapped[str] = mapped_column(nullable=True)
    last_seen: Mapped[datetime.datetime] = mapped_column(nullable=True)

    nights: Mapped[List["Night"]] = relationship(back_populates="device")
    
    def generate_upload_key(self):
        if self.upload_key:
            keys = self.former_keys and [self.former_keys] or []
            keys.append(self.upload_key)
            self.former_keys = ",".join(keys)
        self.upload_key = secrets.token_hex(16)
        return self.upload_key

