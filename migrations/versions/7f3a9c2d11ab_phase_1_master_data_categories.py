# TracePass code note: This module implements the migrations/versions/7f3a9c2d11ab_phase_1_master_data_categories.py part of the application.
"""Phase 1: product category master data.

Revision ID: 7f3a9c2d11ab
Revises: df9fa46b27bc
"""
from alembic import op
import sqlalchemy as sa

revision = "7f3a9c2d11ab"
down_revision = "df9fa46b27bc"
branch_labels = None
depends_on = None


# Code explanation: Implement the `upgrade` operation used by this part of TracePass.
def upgrade():
    op.create_table(
        "product_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["product_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    with op.batch_alter_table("products") as batch_op:
        batch_op.add_column(sa.Column("category_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_products_category_id", ["category_id"], unique=False)
        batch_op.create_foreign_key("fk_products_category_id", "product_categories", ["category_id"], ["id"])


# Code explanation: Implement the `downgrade` operation used by this part of TracePass.
def downgrade():
    with op.batch_alter_table("products") as batch_op:
        batch_op.drop_constraint("fk_products_category_id", type_="foreignkey")
        batch_op.drop_index("ix_products_category_id")
        batch_op.drop_column("category_id")
    op.drop_table("product_categories")
