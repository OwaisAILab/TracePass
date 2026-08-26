# TracePass code note: This module implements the app/models/purchase_order.py part of the application.
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


# Code explanation: Define the Purchase Order data model or application component used by TracePass.
class PurchaseOrder(db.Model):
    """B2B procurement order connecting a buyer to a supplying organization.

    ``from_org_id`` is the BUYER and ``to_org_id`` is the SUPPLIER/FULFILLER.
    The model can be used for raw-material procurement as well as finished
    product replenishment. ``material_id`` identifies the requested raw
    material; ``product_id`` links the procurement to the passport/product
    whose supply-chain story is being built.
    """
    __tablename__ = "purchase_orders"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `po_number` stores this model attribute in the SQL database.
    po_number = db.Column(db.String(20), unique=True, nullable=False)
    # Database field: `product_id` stores this model attribute in the SQL database.
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    # Database field: `material_id` stores this model attribute in the SQL database.
    material_id = db.Column(db.Integer, db.ForeignKey("materials.id"), nullable=True)
    # Database field: `from_org_id` stores this model attribute in the SQL database.
    from_org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    # Database field: `to_org_id` stores this model attribute in the SQL database.
    to_org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    # Database field: `quantity` stores this model attribute in the SQL database.
    quantity = db.Column(db.Integer, nullable=False)
    # Database field: `status` stores this model attribute in the SQL database.
    status = db.Column(db.String(30), default=PO_REQUESTED, nullable=False)
    # Database field: `requested_delivery_date` stores this model attribute in the SQL database.
    requested_delivery_date = db.Column(db.Date, nullable=True)
    # Database field: `confirmed_quantity` stores this model attribute in the SQL database.
    confirmed_quantity = db.Column(db.Integer, nullable=True)
    # Database field: `confirmed_supply_date` stores this model attribute in the SQL database.
    confirmed_supply_date = db.Column(db.Date, nullable=True)
    # Database field: `expected_delivery_date` stores this model attribute in the SQL database.
    expected_delivery_date = db.Column(db.Date, nullable=True)
    # Database field: `supplier_notes` stores this model attribute in the SQL database.
    supplier_notes = db.Column(db.Text, nullable=True)
    # Database field: `rejection_reason` stores this model attribute in the SQL database.
    rejection_reason = db.Column(db.Text, nullable=True)
    # Database field: `requested_by_user_id` stores this model attribute in the SQL database.
    requested_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # Database field: `responded_by_user_id` stores this model attribute in the SQL database.
    responded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    # Database field: `responded_at` stores this model attribute in the SQL database.
    responded_at = db.Column(db.DateTime, nullable=True)
    # Database field: `dispatched_at` stores this model attribute in the SQL database.
    dispatched_at = db.Column(db.DateTime, nullable=True)
    # Database field: `delivered_at` stores this model attribute in the SQL database.
    delivered_at = db.Column(db.DateTime, nullable=True)
    # Database field: `received_at` stores this model attribute in the SQL database.
    received_at = db.Column(db.DateTime, nullable=True)
    # Database field: `notes` stores this model attribute in the SQL database.
    notes = db.Column(db.Text, nullable=True)
    # Database field: `agreed_unit_price` stores this model attribute in the SQL database.
    agreed_unit_price = db.Column(db.Float, nullable=True)
    # Database field: `agreed_total_price` stores this model attribute in the SQL database.
    agreed_total_price = db.Column(db.Float, nullable=True)
    # Database field: `agreed_currency` stores this model attribute in the SQL database.
    agreed_currency = db.Column(db.String(10), nullable=False, default="PKR")
    # Database field: `created_at` stores this model attribute in the SQL database.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # Database field: `updated_at` stores this model attribute in the SQL database.
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    product = db.relationship("Product")
    material = db.relationship("Material")
    from_org = db.relationship("Organization", foreign_keys=[from_org_id])
    to_org = db.relationship("Organization", foreign_keys=[to_org_id])
    requested_by = db.relationship("User", foreign_keys=[requested_by_user_id])
    responded_by = db.relationship("User", foreign_keys=[responded_by_user_id])
    shipments = db.relationship("Shipment", back_populates="purchase_order", lazy="dynamic")
    offers = db.relationship("PurchaseOrderOffer", back_populates="purchase_order", order_by="PurchaseOrderOffer.created_at.asc()", cascade="all, delete-orphan")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<PurchaseOrder {self.po_number} status={self.status}>"
