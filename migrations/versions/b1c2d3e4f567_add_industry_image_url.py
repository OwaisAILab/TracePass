# TracePass code note: This module implements the migrations/versions/b1c2d3e4f567_add_industry_image_url.py part of the application.
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


# Code explanation: Implement the `upgrade` operation used by this part of TracePass.
def upgrade():
    with op.batch_alter_table("industries", schema=None) as batch_op:
        batch_op.add_column(sa.Column("image_url", sa.String(length=255), nullable=True))


# Code explanation: Implement the `downgrade` operation used by this part of TracePass.
def downgrade():
    with op.batch_alter_table("industries", schema=None) as batch_op:
        batch_op.drop_column("image_url")
