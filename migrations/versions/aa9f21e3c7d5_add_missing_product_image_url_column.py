
"""Add missing products.image_url column

The Product model has always defined `image_url`, but no prior migration
actually created it on the `products` table (it was only ever mentioned in
a comment on z9f0e1d2c3b4). This adds it, safely, for databases that are
missing it.

Revision ID: aa9f21e3c7d5
Revises: adcf47548622
Create Date: 2026-08-24 20:30:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "aa9f21e3c7d5"
down_revision = "adcf47548622"
branch_labels = None
depends_on = None


#  Checks a condition and returns a boolean result used by the application logic.
def _has_column(bind, table, column):
    return column in {c["name"] for c in inspect(bind).get_columns(table)}


#  Applies this database migration by creating or changing the required database structures.
def upgrade():
    bind = op.get_bind()
    if not _has_column(bind, "products", "image_url"):
        with op.batch_alter_table("products") as batch_op:
            batch_op.add_column(sa.Column("image_url", sa.String(length=500), nullable=True))


#  Reverses this database migration to return the schema to the previous version.
def downgrade():
    bind = op.get_bind()
    if _has_column(bind, "products", "image_url"):
        with op.batch_alter_table("products") as batch_op:
            batch_op.drop_column("image_url")
