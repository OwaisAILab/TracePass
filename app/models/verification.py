# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
from datetime import datetime, timezone
from app.extensions import db


# What this code does: Defines the VerificationLog class, grouping related data and behavior used by this part of the application.
class VerificationLog(db.Model):
    """Append-only record of every public passport verification attempt."""

    __tablename__ = "verification_logs"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    passport_code = db.Column(db.String(50), nullable=False, index=True)
    result = db.Column(db.String(20), nullable=False)  # verified | invalid | unpublished
    verified_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)

    product = db.relationship("Product", backref=db.backref("verification_logs", lazy="dynamic"))

    # What this code does: Implements the   repr   logic used by this part of the TracePass application.
    def __repr__(self):
        return f"<VerificationLog {self.passport_code} {self.result}>" 
