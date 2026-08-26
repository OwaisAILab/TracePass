# TracePass code note: This module implements the app/models/shipment.py part of the application.
from datetime import datetime, timezone
from app.extensions import db

SHIPMENT_PENDING = "pending"
SHIPMENT_IN_TRANSIT = "in_transit"
SHIPMENT_DELIVERED = "delivered"
SHIPMENT_DELAYED = "delayed"
SHIPMENT_STATUSES = [SHIPMENT_PENDING, SHIPMENT_IN_TRANSIT, SHIPMENT_DELIVERED, SHIPMENT_DELAYED]


# Code explanation: Define the Shipment data model or application component used by TracePass.
class Shipment(db.Model):
    __tablename__ = "shipments"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `purchase_order_id` stores this model attribute in the SQL database.
    purchase_order_id = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"), nullable=True)
    # Database field: `batch_id` stores this model attribute in the SQL database.
    batch_id = db.Column(db.Integer, db.ForeignKey("product_batches.id"), nullable=True)
    # Database field: `material_id` stores this model attribute in the SQL database.
    material_id = db.Column(db.Integer, db.ForeignKey("materials.id"), nullable=True)
    # Database field: `quantity` stores this model attribute in the SQL database.
    quantity = db.Column(db.Integer, nullable=True)
    # Database field: `from_org_id` stores this model attribute in the SQL database.
    from_org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)
    # Database field: `to_org_id` stores this model attribute in the SQL database.
    to_org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)
    # Database field: `tracking_no` stores this model attribute in the SQL database.
    tracking_no = db.Column(db.String(100), nullable=True)
    # Database field: `status` stores this model attribute in the SQL database.
    status = db.Column(db.String(20), default=SHIPMENT_PENDING, nullable=False)
    # Database field: `shipped_date` stores this model attribute in the SQL database.
    shipped_date = db.Column(db.Date, nullable=True)
    # Database field: `expected_delivery_date` stores this model attribute in the SQL database.
    expected_delivery_date = db.Column(db.Date, nullable=True)
    # Database field: `received_date` stores this model attribute in the SQL database.
    received_date = db.Column(db.Date, nullable=True)
    # Database field: `created_at` stores this model attribute in the SQL database.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    purchase_order = db.relationship("PurchaseOrder", back_populates="shipments")
    batch = db.relationship("ProductBatch", backref=db.backref("shipments", lazy="dynamic"))
    material = db.relationship("Material")
    from_org = db.relationship("Organization", foreign_keys=[from_org_id])
    to_org = db.relationship("Organization", foreign_keys=[to_org_id])

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<Shipment {self.tracking_no or self.id} status={self.status}>"
