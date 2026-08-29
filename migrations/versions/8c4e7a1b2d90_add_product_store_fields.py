"""Legacy revision retained only to preserve the Alembic history.

The online-store product price field is intentionally not created in the final
TracePass release. Existing databases are cleaned by the final hardening
migration.
"""
revision = "8c4e7a1b2d90"
down_revision = "7f3a9c2d11ab"
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass
