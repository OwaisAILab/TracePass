# TracePass code note: This module implements the app/models/recall_incident.py part of the application.
from datetime import datetime, timezone
from app.extensions import db

RECALL_OPEN = "open"
RECALL_IN_PROGRESS = "in_progress"
RECALL_CLOSED = "closed"
RECALL_STATUSES = [RECALL_OPEN, RECALL_IN_PROGRESS, RECALL_CLOSED]

INCIDENT_OPEN = "open"
INCIDENT_INVESTIGATING = "investigating"
INCIDENT_RESOLVED = "resolved"
INCIDENT_STATUSES = [INCIDENT_OPEN, INCIDENT_INVESTIGATING, INCIDENT_RESOLVED]


# Code explanation: Define the Recall data model or application component used by TracePass.
class Recall(db.Model):
    __tablename__ = "recalls"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `product_id` stores this model attribute in the SQL database.
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    # Database field: `batch_id` stores this model attribute in the SQL database.
    batch_id = db.Column(db.Integer, db.ForeignKey("product_batches.id"), nullable=True)
    # Database field: `reason` stores this model attribute in the SQL database.
    reason = db.Column(db.Text, nullable=False)
    # Database field: `status` stores this model attribute in the SQL database.
    status = db.Column(db.String(20), default=RECALL_OPEN, nullable=False)
    # Database field: `issued_by_user_id` stores this model attribute in the SQL database.
    issued_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # Database field: `issued_at` stores this model attribute in the SQL database.
    issued_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    # Database field: `closed_at` stores this model attribute in the SQL database.
    closed_at = db.Column(db.DateTime, nullable=True)

    product = db.relationship("Product", backref=db.backref("recalls", lazy="dynamic"))
    batch = db.relationship("ProductBatch")
    issued_by = db.relationship("User")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<Recall product={self.product_id} status={self.status}>"


# Code explanation: Define the Incident data model or application component used by TracePass.
class Incident(db.Model):
    __tablename__ = "incidents"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `product_id` stores this model attribute in the SQL database.
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    # Database field: `reported_by_user_id` stores this model attribute in the SQL database.
    reported_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # Database field: `description` stores this model attribute in the SQL database.
    description = db.Column(db.Text, nullable=False)
    # Database field: `status` stores this model attribute in the SQL database.
    status = db.Column(db.String(20), default=INCIDENT_OPEN, nullable=False)
    # Database field: `reported_at` stores this model attribute in the SQL database.
    reported_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    # Database field: `resolved_at` stores this model attribute in the SQL database.
    resolved_at = db.Column(db.DateTime, nullable=True)
    # Database field: `resolution_notes` stores this model attribute in the SQL database.
    resolution_notes = db.Column(db.Text, nullable=True)

    product = db.relationship("Product", backref=db.backref("incidents", lazy="dynamic"))
    reported_by = db.relationship("User")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<Incident product={self.product_id} status={self.status}>"
