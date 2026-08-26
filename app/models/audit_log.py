# TracePass code note: This module implements the app/models/audit_log.py part of the application.
from datetime import datetime, timezone
from app.extensions import db


# Code explanation: Define the Audit Log data model or application component used by TracePass.
class AuditLog(db.Model):
    """
    Append-only log of significant actions. Never updated or deleted.
    Written automatically via SQLAlchemy event listeners (see
    app/reporting/audit.py) so route handlers don't need to remember to
    call it manually — that's what makes coverage reliable.
    """

    __tablename__ = "audit_logs"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `user_id` stores this model attribute in the SQL database.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    # Database field: `action` stores this model attribute in the SQL database.
    action = db.Column(db.String(20), nullable=False)  # create | update | delete
    # Database field: `entity_type` stores this model attribute in the SQL database.
    entity_type = db.Column(db.String(50), nullable=False)  # e.g. "Product", "Certificate"
    # Database field: `entity_id` stores this model attribute in the SQL database.
    entity_id = db.Column(db.Integer, nullable=True)
    # Database field: `old_value` stores this model attribute in the SQL database.
    old_value = db.Column(db.Text, nullable=True)
    # Database field: `new_value` stores this model attribute in the SQL database.
    new_value = db.Column(db.Text, nullable=True)
    # Database field: `created_at` stores this model attribute in the SQL database.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship("User")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<AuditLog {self.action} {self.entity_type}#{self.entity_id}>"
