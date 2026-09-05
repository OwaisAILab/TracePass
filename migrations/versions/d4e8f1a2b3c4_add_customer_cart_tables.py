
"""Legacy revision retained only to preserve the Alembic history.

Customer cart/order functionality was removed from the final TracePass
Digital Product Passport scope, so this historical revision is now a no-op.
Existing databases are cleaned by the final hardening migration.
"""
revision = "d4e8f1a2b3c4"
down_revision = "c3d7e9f2a114"
branch_labels = None
depends_on = None

#  Applies this database migration by creating or changing the required database structures.
def upgrade():
    pass

#  Reverses this database migration to return the schema to the previous version.
def downgrade():
    pass
