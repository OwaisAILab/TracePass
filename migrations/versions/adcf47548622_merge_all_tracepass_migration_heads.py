
"""Merge all TracePass migration heads

Revision ID: adcf47548622
Revises: 8c4e7a1b2d90, d4e8f1a2b3c4, f7b8c9d0e123, z9f0e1d2c3b4
Create Date: 2026-08-24 19:22:09.222177

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'adcf47548622'
down_revision = ('8c4e7a1b2d90', 'd4e8f1a2b3c4', 'f7b8c9d0e123', 'z9f0e1d2c3b4')
branch_labels = None
depends_on = None


#  Applies this database migration by creating or changing the required database structures.
def upgrade():
    pass


#  Reverses this database migration to return the schema to the previous version.
def downgrade():
    pass
