# TracePass code note: This module implements the app/models/supply_chain_event.py part of the application.
from datetime import datetime, timezone
from app.extensions import db

EVENT_MANUFACTURED = "manufactured"
EVENT_QUALITY_CHECK = "quality_check"
EVENT_SHIPPED = "shipped"
EVENT_DELIVERED = "delivered"
EVENT_RECEIVED = "received"
EVENT_SOLD = "sold"
EVENT_RECALLED = "recalled"
EVENT_OTHER = "other"

EVENT_TYPES = [
    EVENT_MANUFACTURED,
    EVENT_QUALITY_CHECK,
    EVENT_SHIPPED,
    EVENT_DELIVERED,
    EVENT_RECEIVED,
    EVENT_SOLD,
    EVENT_RECALLED,
    EVENT_OTHER,
]


# Code explanation: Define the Supply Chain Event data model or application component used by TracePass.
class SupplyChainEvent(db.Model):
    __tablename__ = "supply_chain_events"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `product_id` stores this model attribute in the SQL database.
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    # Database field: `batch_id` stores this model attribute in the SQL database.
    batch_id = db.Column(db.Integer, db.ForeignKey("product_batches.id"), nullable=True)
    # Database field: `organization_id` stores this model attribute in the SQL database.
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)
    # Database field: `event_type` stores this model attribute in the SQL database.
    event_type = db.Column(db.String(30), nullable=False)
    # Database field: `location` stores this model attribute in the SQL database.
    location = db.Column(db.String(150), nullable=True)
    # Database field: `event_date` stores this model attribute in the SQL database.
    event_date = db.Column(db.DateTime, nullable=False)
    # Database field: `notes` stores this model attribute in the SQL database.
    notes = db.Column(db.Text, nullable=True)
    # Database field: `recorded_by_user_id` stores this model attribute in the SQL database.
    recorded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    # Database field: `created_at` stores this model attribute in the SQL database.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    product = db.relationship("Product", backref=db.backref("supply_chain_events", lazy="dynamic"))
    batch = db.relationship("ProductBatch", back_populates="events")
    organization = db.relationship("Organization")
    recorded_by = db.relationship("User")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<SupplyChainEvent {self.event_type} product={self.product_id}>"
