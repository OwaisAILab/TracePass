# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
"""add image_url to industries

Revision ID: b1c2d3e4f567
Revises: aa9f21e3c7d5
Create Date: 2026-08-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b1c2d3e4f567"
down_revision = "aa9f21e3c7d5"
branch_labels = None
depends_on = None


# What this code does: Applies this database migration by creating or changing the required database structures.
def upgrade():
    with op.batch_alter_table("industries", schema=None) as batch_op:
        batch_op.add_column(sa.Column("image_url", sa.String(length=255), nullable=True))


# What this code does: Reverses this database migration to return the schema to the previous version.
def downgrade():
    with op.batch_alter_table("industries", schema=None) as batch_op:
        batch_op.drop_column("image_url")
