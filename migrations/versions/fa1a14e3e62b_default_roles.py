"""default roles

Revision ID: fa1a14e3e62b
Revises: 07a1d14c6d54
Create Date: 2025-11-18 13:19:23.783020

"""
from alembic import op
import sqlalchemy as sa
from flask_security.models import fsqla_v3 as fsqla

from mothmonitor.models import Role

# revision identifiers, used by Alembic.
revision = 'fa1a14e3e62b'
down_revision = '07a1d14c6d54'
branch_labels = None
depends_on = None


def upgrade():
    op.bulk_insert(
        Role.__table__,
        [
            {
                'id': 1,
                'name': "Admin",
                'description': "Admin",
                'permissions': ["admin", "research", "site"]
            },
            {
                'id': 2,
                'name': "Research",
                'description': "Research",
                'permissions': ["research", "site"]
            },
            {
                'id': 3,
                'name': "Site",
                'description': "Site",
                'permissions': ["site"]
            }
        ]
    )
    op.bulk_insert(
        fsqla.FsModels.roles_users,
        [
            {"user_id": 1, "role_id": 1}
        ]
    )

def downgrade():
    op.execute("DELETE FROM Role")
