# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
"""Record the user who triggered each compliance check."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "f7b8c9d0e123"
down_revision = "f6a7b8c9d012"
branch_labels = None
depends_on = None


# What this code does: Checks a condition and returns a boolean result used by the application logic.
def _has_column(bind, table, column):
    return column in {c["name"] for c in inspect(bind).get_columns(table)}


# What this code does: Applies this database migration by creating or changing the required database structures.
def upgrade():
    bind = op.get_bind()
    if not _has_column(bind, "compliance_checks", "checked_by_user_id"):
        with op.batch_alter_table("compliance_checks", schema=None) as batch_op:
            batch_op.add_column(
                sa.Column("checked_by_user_id", sa.Integer(), nullable=True)
            )
            batch_op.create_foreign_key(
                "fk_compliance_check_user",
                "users",
                ["checked_by_user_id"],
                ["id"],
            )


# What this code does: Reverses this database migration to return the schema to the previous version.
def downgrade():
    bind = op.get_bind()
    if _has_column(bind, "compliance_checks", "checked_by_user_id"):
        with op.batch_alter_table("compliance_checks", schema=None) as batch_op:
            batch_op.drop_constraint(
                "fk_compliance_check_user", type_="foreignkey"
            )
            batch_op.drop_column("checked_by_user_id")
