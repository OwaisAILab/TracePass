
from datetime import datetime, timezone
from app.extensions import db

SHIPMENT_PENDING = "pending"
SHIPMENT_IN_TRANSIT = "in_transit"
SHIPMENT_DELIVERED = "delivered"
SHIPMENT_DELAYED = "delayed"
SHIPMENT_STATUSES = [SHIPMENT_PENDING, SHIPMENT_IN_TRANSIT, SHIPMENT_DELIVERED, SHIPMENT_DELAYED]


# Defines the shipment class and groups its related data and behavior.
class Shipment(db.Model):
    __tablename__ = "shipments"

    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"), nullable=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("product_batches.id"), nullable=True)
    material_id = db.Column(db.Integer, db.ForeignKey("materials.id"), nullable=True)
    quantity = db.Column(db.Integer, nullable=True)
    from_org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)
    to_org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)
    tracking_no = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default=SHIPMENT_PENDING, nullable=False)
    shipped_date = db.Column(db.Date, nullable=True)
    expected_delivery_date = db.Column(db.Date, nullable=True)
    received_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    purchase_order = db.relationship("PurchaseOrder", back_populates="shipments")
    batch = db.relationship("ProductBatch", backref=db.backref("shipments", lazy="dynamic"))
    material = db.relationship("Material")
    from_org = db.relationship("Organization", foreign_keys=[from_org_id])
    to_org = db.relationship("Organization", foreign_keys=[to_org_id])

# Provides the internal repr helper used by this module's workflow.
    def __repr__(self):
        return f"<Shipment {self.tracking_no or self.id} status={self.status}>"
