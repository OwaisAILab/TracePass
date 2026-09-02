from datetime import datetime, timezone
from app.extensions import db


LIFECYCLE_EVENT_TYPES = [
    "reused",
    "refurbished",
    "repaired",
    "recycled",
    "recovered",
    "disposed",
    "end_of_life",
    "other",
]


class LifecycleEvent(db.Model):
    """Post-manufacturing and end-of-life events for a product passport."""

    __tablename__ = "lifecycle_events"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    event_type = db.Column(db.String(30), nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)
    location = db.Column(db.String(150), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    recorded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    product = db.relationship("Product", backref=db.backref("lifecycle_events", lazy="dynamic"))
    organization = db.relationship("Organization")
    recorded_by = db.relationship("User")

    def __repr__(self):
        return f"<LifecycleEvent {self.event_type} product={self.product_id}>"
