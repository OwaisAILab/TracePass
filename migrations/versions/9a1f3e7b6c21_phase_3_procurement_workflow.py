
"""Phase 3 procurement workflow: raw-material purchase orders and shipments.

Revision ID: 9a1f3e7b6c21
Revises: 8c4e7a1b2d90
"""
from alembic import op
import sqlalchemy as sa

revision = "9a1f3e7b6c21"
down_revision = "7f3a9c2d11ab"
branch_labels = None
depends_on = None


#  Applies this database migration by creating or changing the required database structures.
def upgrade():
    # The procurement model was introduced in the application code, but the
    # previous Phase 3 package did not create the purchase_orders table.
    # Create the complete base table here before adding the workflow fields
    # to shipments. This migration is now based on the Phase 1.1 head so a
    # database already upgraded through Phase 1/2/3/5 can migrate cleanly.
    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("po_number", sa.String(length=20), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("material_id", sa.Integer(), nullable=True),
        sa.Column("from_org_id", sa.Integer(), nullable=False),
        sa.Column("to_org_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("requested_delivery_date", sa.Date(), nullable=True),
        sa.Column("confirmed_quantity", sa.Integer(), nullable=True),
        sa.Column("confirmed_supply_date", sa.Date(), nullable=True),
        sa.Column("expected_delivery_date", sa.Date(), nullable=True),
        sa.Column("supplier_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=False),
        sa.Column("responded_by_user_id", sa.Integer(), nullable=True),
        sa.Column("responded_at", sa.DateTime(), nullable=True),
        sa.Column("dispatched_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"]),
        sa.ForeignKeyConstraint(["from_org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["to_org_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["responded_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("po_number"),
    )

    with op.batch_alter_table("shipments", schema=None) as batch_op:
        batch_op.alter_column("batch_id", existing_type=sa.Integer(), nullable=True)
        batch_op.add_column(sa.Column("purchase_order_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("material_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("quantity", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_shipments_purchase_order", "purchase_orders", ["purchase_order_id"], ["id"])
        batch_op.create_foreign_key("fk_shipments_material", "materials", ["material_id"], ["id"])


#  Reverses this database migration to return the schema to the previous version.
def downgrade():
    with op.batch_alter_table("shipments", schema=None) as batch_op:
        batch_op.drop_constraint("fk_shipments_material", type_="foreignkey")
        batch_op.drop_constraint("fk_shipments_purchase_order", type_="foreignkey")
        batch_op.drop_column("quantity")
        batch_op.drop_column("material_id")
        batch_op.drop_column("purchase_order_id")
        batch_op.alter_column("batch_id", existing_type=sa.Integer(), nullable=False)

    op.drop_table("purchase_orders")
