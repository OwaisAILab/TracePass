# TracePass code note: This module implements the migrations/versions/d4e8f1a2b3c4_add_customer_cart_tables.py part of the application.
"""Legacy revision retained only to preserve the Alembic history.

Customer cart/order functionality was removed from the final TracePass
Digital Product Passport scope, so this historical revision is now a no-op.
Existing databases are cleaned by the final hardening migration.
"""
revision = "d4e8f1a2b3c4"
down_revision = "c3d7e9f2a114"
branch_labels = None
depends_on = None

# Code explanation: Implement the `upgrade` operation used by this part of TracePass.
def upgrade():
    pass

# Code explanation: Implement the `downgrade` operation used by this part of TracePass.
def downgrade():
    pass
