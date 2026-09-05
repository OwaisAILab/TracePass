
"""add controlled organizational registration requests

Revision ID: c4d5e6f7a890
Revises: b1c2d3e4f567
Create Date: 2026-08-29

This migration adds the public Contact Us -> Request an Account workflow.
"""
from alembic import op
import sqlalchemy as sa

revision = "c4d5e6f7a890"
down_revision = "b1c2d3e4f567"
branch_labels = None
depends_on = None


#  Applies this database migration by creating or changing the required database structures.
def upgrade():
    op.create_table(
        "registration_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("requested_role", sa.String(length=30), nullable=False),
        sa.Column("organization_name", sa.String(length=150), nullable=False),
        sa.Column("registration_no", sa.String(length=100), nullable=True),
        sa.Column("organization_type", sa.String(length=30), nullable=False),
        sa.Column("organization_email", sa.String(length=120), nullable=True),
        sa.Column("organization_phone", sa.String(length=30), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_registration_requests_email", "registration_requests", ["email"])
    op.create_index("ix_registration_requests_status", "registration_requests", ["status"])


#  Reverses this database migration to return the schema to the previous version.
def downgrade():
    op.drop_index("ix_registration_requests_status", table_name="registration_requests")
    op.drop_index("ix_registration_requests_email", table_name="registration_requests")
    op.drop_table("registration_requests")
