# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
"""Legacy revision retained only to preserve the Alembic history.

The online-store product price field is intentionally not created in the final
TracePass release. Existing databases are cleaned by the final hardening
migration.
"""
revision = "8c4e7a1b2d90"
down_revision = "7f3a9c2d11ab"
branch_labels = None
depends_on = None

# What this code does: Applies this database migration by creating or changing the required database structures.
def upgrade():
    pass

# What this code does: Reverses this database migration to return the schema to the previous version.
def downgrade():
    pass
