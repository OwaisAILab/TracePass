# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
"""Add authenticity documents for registration requests.

Revision ID: c5e6f7a89012
Revises: c4d5e6f7a890
"""
from alembic import op
import sqlalchemy as sa

revision = "c5e6f7a89012"
down_revision = "c4d5e6f7a890"
branch_labels = None
depends_on = None


# What this code does: Applies this database migration by creating or changing the required database structures.
def upgrade():
    op.create_table(
        "registration_request_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("registration_request_id", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(length=100), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["registration_request_id"], ["registration_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_registration_request_documents_registration_request_id", "registration_request_documents", ["registration_request_id"], unique=False)


# What this code does: Reverses this database migration to return the schema to the previous version.
def downgrade():
    op.drop_index("ix_registration_request_documents_registration_request_id", table_name="registration_request_documents")
    op.drop_table("registration_request_documents")
