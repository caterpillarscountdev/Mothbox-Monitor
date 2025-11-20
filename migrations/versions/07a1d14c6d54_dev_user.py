"""dev-user

Revision ID: 07a1d14c6d54
Revises: 5eae3964f3e1
Create Date: 2025-11-18 12:22:41.309479

"""
from alembic import op
import sqlalchemy as sa

from flask_security.utils import hash_password
from mothmonitor.models import User


# revision identifiers, used by Alembic.
revision = '07a1d14c6d54'
down_revision = '5eae3964f3e1'
branch_labels = None
depends_on = None


def upgrade():
    op.bulk_insert(
        User.__table__,
        [
            {
                'id': 1,
                'active': True,
                'fs_uniquifier': 1,
                'email': 'test@example.com',
                'name': 'Test User',
                'password': hash_password('test')
             }
        ]
    )
    

def downgrade():
    op.execute("DELETE FROM user WHERE email = 'test@example.com'")
