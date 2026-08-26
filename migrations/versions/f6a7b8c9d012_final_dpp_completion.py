# TracePass code note: This module implements the migrations/versions/f6a7b8c9d012_final_dpp_completion.py part of the application.
"""Complete general DPP controls: verification history, sustainability and lifecycle data.

This migration is intentionally safe when upgrading from the final hardening
migration, which already owns certificate review metadata.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "f6a7b8c9d012"
down_revision = "aa11bb22cc33"
branch_labels = None
depends_on = None


# Code explanation: Implement the `has table` operation used by this part of TracePass.
def _has_table(bind, name):
    return inspect(bind).has_table(name)


# Code explanation: Implement the `has column` operation used by this part of TracePass.
def _has_column(bind, table, column):
    return column in {c["name"] for c in inspect(bind).get_columns(table)}


# Code explanation: Implement the `upgrade` operation used by this part of TracePass.
def upgrade():
    bind = op.get_bind()

    # The final hardening migration owns certificate review/ownership fields.
    # Do not add them again here; this branch only adds DPP lifecycle controls.

    if not _has_column(bind, "products", "sustainability_data"):
        with op.batch_alter_table("products", schema=None) as batch_op:
            batch_op.add_column(
                sa.Column("sustainability_data", sa.Text(), nullable=True)
            )

    if not _has_table(bind, "verification_logs"):
        op.create_table(
            "verification_logs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("product_id", sa.Integer(), nullable=True),
            sa.Column("passport_code", sa.String(length=50), nullable=False),
            sa.Column("result", sa.String(length=20), nullable=False),
            sa.Column("verified_at", sa.DateTime(), nullable=False),
            sa.Column("ip_address", sa.String(length=64), nullable=True),
            sa.Column("user_agent", sa.String(length=500), nullable=True),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        )
        op.create_index(
            "ix_verification_logs_passport_code",
            "verification_logs",
            ["passport_code"],
            unique=False,
        )

    if not _has_table(bind, "lifecycle_events"):
        op.create_table(
            "lifecycle_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("product_id", sa.Integer(), nullable=False),
            sa.Column("event_type", sa.String(length=30), nullable=False),
            sa.Column("event_date", sa.DateTime(), nullable=False),
            sa.Column("organization_id", sa.Integer(), nullable=True),
            sa.Column("location", sa.String(length=150), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("recorded_by_user_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
            sa.ForeignKeyConstraint(["recorded_by_user_id"], ["users.id"]),
        )


# Code explanation: Implement the `downgrade` operation used by this part of TracePass.
def downgrade():
    bind = op.get_bind()
    if _has_table(bind, "lifecycle_events"):
        op.drop_table("lifecycle_events")
    if _has_table(bind, "verification_logs"):
        if any(
            i["name"] == "ix_verification_logs_passport_code"
            for i in inspect(bind).get_indexes("verification_logs")
        ):
            op.drop_index(
                "ix_verification_logs_passport_code",
                table_name="verification_logs",
            )
        op.drop_table("verification_logs")
    if _has_column(bind, "products", "sustainability_data"):
        with op.batch_alter_table("products", schema=None) as batch_op:
            batch_op.drop_column("sustainability_data")
