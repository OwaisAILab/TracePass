
from datetime import datetime, timezone
from app.extensions import db

PO_REQUESTED = "requested"
PO_CONFIRMED = "confirmed"
PO_REJECTED = "rejected"
PO_PREPARING = "preparing"
PO_READY = "ready_for_dispatch"
PO_SHIPPED = "shipped"
PO_IN_TRANSIT = "in_transit"
PO_DELIVERED = "delivered"
PO_RECEIVED = "received"
PO_CANCELLED = "cancelled"
PO_STATUSES = [
    PO_REQUESTED, PO_CONFIRMED, PO_REJECTED, PO_PREPARING, PO_READY,
    PO_SHIPPED, PO_IN_TRANSIT, PO_DELIVERED, PO_RECEIVED, PO_CANCELLED,
]


# Defines the purchase order class and groups its related data and behavior.
class PurchaseOrder(db.Model):
    """B2B procurement order connecting a buyer to a supplying organization.

    ``from_org_id`` is the BUYER and ``to_org_id`` is the SUPPLIER/FULFILLER.
    The model can be used for raw-material procurement as well as finished
    product replenishment. ``material_id`` identifies the requested raw
    material; ``product_id`` links the procurement to the passport/product
    whose supply-chain story is being built.
    """
    __tablename__ = "purchase_orders"

    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(20), unique=True, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    material_id = db.Column(db.Integer, db.ForeignKey("materials.id"), nullable=True)
    from_org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    to_org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), default=PO_REQUESTED, nullable=False)
    requested_delivery_date = db.Column(db.Date, nullable=True)
    confirmed_quantity = db.Column(db.Integer, nullable=True)
    confirmed_supply_date = db.Column(db.Date, nullable=True)
    expected_delivery_date = db.Column(db.Date, nullable=True)
    supplier_notes = db.Column(db.Text, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    requested_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    responded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    responded_at = db.Column(db.DateTime, nullable=True)
    dispatched_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    received_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    agreed_unit_price = db.Column(db.Float, nullable=True)
    agreed_total_price = db.Column(db.Float, nullable=True)
    agreed_currency = db.Column(db.String(10), nullable=False, default="PKR")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    product = db.relationship("Product")
    material = db.relationship("Material")
    from_org = db.relationship("Organization", foreign_keys=[from_org_id])
    to_org = db.relationship("Organization", foreign_keys=[to_org_id])
    requested_by = db.relationship("User", foreign_keys=[requested_by_user_id])
    responded_by = db.relationship("User", foreign_keys=[responded_by_user_id])
    shipments = db.relationship("Shipment", back_populates="purchase_order", lazy="dynamic")
    offers = db.relationship("PurchaseOrderOffer", back_populates="purchase_order", order_by="PurchaseOrderOffer.created_at.asc()", cascade="all, delete-orphan")

# Provides the internal repr helper used by this module's workflow.
    def __repr__(self):
        return f"<PurchaseOrder {self.po_number} status={self.status}>"
