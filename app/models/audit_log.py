
from datetime import datetime, timezone
from app.extensions import db


# Defines the audit log class and groups its related data and behavior.
class AuditLog(db.Model):
    """
    Append-only log of significant actions. Never updated or deleted.
    Written automatically via SQLAlchemy event listeners (see
    app/reporting/audit.py) so route handlers don't need to remember to
    call it manually — that's what makes coverage reliable.
    """

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(20), nullable=False)  # create | update | delete
    entity_type = db.Column(db.String(50), nullable=False)  # e.g. "Product", "Certificate"
    entity_id = db.Column(db.Integer, nullable=True)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship("User")

# Provides the internal repr helper used by this module's workflow.
    def __repr__(self):
        return f"<AuditLog {self.action} {self.entity_type}#{self.entity_id}>"
