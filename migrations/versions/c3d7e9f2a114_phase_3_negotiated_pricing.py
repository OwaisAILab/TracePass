"""Phase 3: negotiated purchase prices and supplier offering cleanup."""
from alembic import op
import sqlalchemy as sa

revision = "c3d7e9f2a114"
down_revision = "b7c2d4e8f901"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("supplier_materials", schema=None) as batch_op:
        batch_op.drop_column("price_per_unit")

    with op.batch_alter_table("purchase_orders", schema=None) as batch_op:
        batch_op.add_column(sa.Column("agreed_unit_price", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("agreed_total_price", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("agreed_currency", sa.String(length=10), nullable=False, server_default="PKR"))

    op.create_table(
        "purchase_order_offers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=False),
        sa.Column("offered_by_user_id", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("confirmed_supply_date", sa.Date(), nullable=True),
        sa.Column("expected_delivery_date", sa.Date(), nullable=True),
        sa.Column("total_price", sa.Float(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["offered_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Existing Phase 3 orders have no negotiated price. Leave them untouched.
    # The server_default is only for schema compatibility and is removed below.
    with op.batch_alter_table("purchase_orders", schema=None) as batch_op:
        batch_op.alter_column("agreed_currency", server_default=None)


def downgrade():
    op.drop_table("purchase_order_offers")
    with op.batch_alter_table("purchase_orders", schema=None) as batch_op:
        batch_op.drop_column("agreed_currency")
        batch_op.drop_column("agreed_total_price")
        batch_op.drop_column("agreed_unit_price")
    with op.batch_alter_table("supplier_materials", schema=None) as batch_op:
        batch_op.add_column(sa.Column("price_per_unit", sa.Float(), nullable=True))
