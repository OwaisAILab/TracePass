# TracePass code note: This module implements the migrations/versions/b7c2d4e8f901_supplier_material_offerings.py part of the application.
"""Phase 3: supplier material offerings for material-based sourcing."""
from alembic import op
import sqlalchemy as sa

revision = "b7c2d4e8f901"
down_revision = "9a1f3e7b6c21"
branch_labels = None
depends_on = None


# Code explanation: Implement the `upgrade` operation used by this part of TracePass.
def upgrade():
    op.create_table(
        "supplier_materials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("material_id", sa.Integer(), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("minimum_order_qty", sa.Float(), nullable=True),
        sa.Column("lead_time_days", sa.Integer(), nullable=True),
        sa.Column("price_per_unit", sa.Float(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"]),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("supplier_id", "material_id", name="uq_supplier_material"),
    )


# Code explanation: Implement the `downgrade` operation used by this part of TracePass.
def downgrade():
    op.drop_table("supplier_materials")
