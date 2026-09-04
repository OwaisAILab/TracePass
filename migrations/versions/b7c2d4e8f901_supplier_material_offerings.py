# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
"""Phase 3: supplier material offerings for material-based sourcing."""
from alembic import op
import sqlalchemy as sa

revision = "b7c2d4e8f901"
down_revision = "9a1f3e7b6c21"
branch_labels = None
depends_on = None


# What this code does: Applies this database migration by creating or changing the required database structures.
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


# What this code does: Reverses this database migration to return the schema to the previous version.
def downgrade():
    op.drop_table("supplier_materials")
