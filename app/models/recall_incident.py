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


class Recall(db.Model):
    __tablename__ = "recalls"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey("product_batches.id"), nullable=True)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default=RECALL_OPEN, nullable=False)
    issued_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    issued_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    closed_at = db.Column(db.DateTime, nullable=True)

    product = db.relationship("Product", backref=db.backref("recalls", lazy="dynamic"))
    batch = db.relationship("ProductBatch")
    issued_by = db.relationship("User")

    def __repr__(self):
        return f"<Recall product={self.product_id} status={self.status}>"


class Incident(db.Model):
    __tablename__ = "incidents"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    reported_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default=INCIDENT_OPEN, nullable=False)
    reported_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)

    product = db.relationship("Product", backref=db.backref("incidents", lazy="dynamic"))
    reported_by = db.relationship("User")

    def __repr__(self):
        return f"<Incident product={self.product_id} status={self.status}>"
