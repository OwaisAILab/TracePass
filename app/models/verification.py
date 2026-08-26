# TracePass code note: This module implements the app/models/verification.py part of the application.
from datetime import datetime, timezone
from app.extensions import db


# Code explanation: Define the Verification Log data model or application component used by TracePass.
class VerificationLog(db.Model):
    """Append-only record of every public passport verification attempt."""

    __tablename__ = "verification_logs"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `product_id` stores this model attribute in the SQL database.
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    # Database field: `passport_code` stores this model attribute in the SQL database.
    passport_code = db.Column(db.String(50), nullable=False, index=True)
    # Database field: `result` stores this model attribute in the SQL database.
    result = db.Column(db.String(20), nullable=False)  # verified | invalid | unpublished
    # Database field: `verified_at` stores this model attribute in the SQL database.
    verified_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    # Database field: `ip_address` stores this model attribute in the SQL database.
    ip_address = db.Column(db.String(64), nullable=True)
    # Database field: `user_agent` stores this model attribute in the SQL database.
    user_agent = db.Column(db.String(500), nullable=True)

    product = db.relationship("Product", backref=db.backref("verification_logs", lazy="dynamic"))

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<VerificationLog {self.passport_code} {self.result}>" 
