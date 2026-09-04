# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
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


# What this code does: Defines the SupplyChainEvent class, grouping related data and behavior used by this part of the application.
class SupplyChainEvent(db.Model):
    __tablename__ = "supply_chain_events"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey("product_batches.id"), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)
    event_type = db.Column(db.String(30), nullable=False)
    location = db.Column(db.String(150), nullable=True)
    event_date = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    recorded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    product = db.relationship("Product", backref=db.backref("supply_chain_events", lazy="dynamic"))
    batch = db.relationship("ProductBatch", back_populates="events")
    organization = db.relationship("Organization")
    recorded_by = db.relationship("User")

    # What this code does: Implements the   repr   logic used by this part of the TracePass application.
    def __repr__(self):
        return f"<SupplyChainEvent {self.event_type} product={self.product_id}>"
