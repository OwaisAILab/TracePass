"""Add mandatory email OTP verification for registration

Revision ID: emailotp20260902
Revises: c5e6f7a89012
"""

from alembic import op
import sqlalchemy as sa


revision = "emailotp20260902"
down_revision = "c5e6f7a89012"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "email_verifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=120), nullable=False),
        sa.Column("purpose", sa.String(length=40), nullable=False),
        sa.Column("otp_hash", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("file_paths", sa.JSON(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_verifications_email", "email_verifications", ["email"])
    op.create_index("ix_email_verifications_purpose", "email_verifications", ["purpose"])
    op.create_index("ix_email_verifications_expires_at", "email_verifications", ["expires_at"])


def downgrade():
    op.drop_index("ix_email_verifications_expires_at", table_name="email_verifications")
    op.drop_index("ix_email_verifications_purpose", table_name="email_verifications")
    op.drop_index("ix_email_verifications_email", table_name="email_verifications")
    op.drop_table("email_verifications")
