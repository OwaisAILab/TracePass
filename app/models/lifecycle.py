# TracePass code note: This module implements the app/models/lifecycle.py part of the application.
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


# Code explanation: Define the Lifecycle Event data model or application component used by TracePass.
class LifecycleEvent(db.Model):
    """Post-manufacturing and end-of-life events for a product passport."""

    __tablename__ = "lifecycle_events"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `product_id` stores this model attribute in the SQL database.
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    # Database field: `event_type` stores this model attribute in the SQL database.
    event_type = db.Column(db.String(30), nullable=False)
    # Database field: `event_date` stores this model attribute in the SQL database.
    event_date = db.Column(db.DateTime, nullable=False)
    # Database field: `organization_id` stores this model attribute in the SQL database.
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)
    # Database field: `location` stores this model attribute in the SQL database.
    location = db.Column(db.String(150), nullable=True)
    # Database field: `notes` stores this model attribute in the SQL database.
    notes = db.Column(db.Text, nullable=True)
    # Database field: `recorded_by_user_id` stores this model attribute in the SQL database.
    recorded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    # Database field: `created_at` stores this model attribute in the SQL database.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    product = db.relationship("Product", backref=db.backref("lifecycle_events", lazy="dynamic"))
    organization = db.relationship("Organization")
    recorded_by = db.relationship("User")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<LifecycleEvent {self.event_type} product={self.product_id}>"
