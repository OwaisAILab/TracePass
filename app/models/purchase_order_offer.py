# TracePass code note: This module implements the app/models/purchase_order_offer.py part of the application.
from datetime import datetime, timezone
from app.extensions import db

OFFER_PROPOSED = 'proposed'
OFFER_ACCEPTED = 'accepted'
OFFER_REJECTED = 'rejected'
OFFER_SUPERSEDED = 'superseded'

# Code explanation: Define the Purchase Order Offer data model or application component used by TracePass.
class PurchaseOrderOffer(db.Model):
    __tablename__ = 'purchase_order_offers'

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `purchase_order_id` stores this model attribute in the SQL database.
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    # Database field: `offered_by_user_id` stores this model attribute in the SQL database.
    offered_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Database field: `unit_price` stores this model attribute in the SQL database.
    unit_price = db.Column(db.Float, nullable=False)
    # Database field: `currency` stores this model attribute in the SQL database.
    currency = db.Column(db.String(10), nullable=False, default='PKR')
    # Database field: `quantity` stores this model attribute in the SQL database.
    quantity = db.Column(db.Integer, nullable=False)
    # Database field: `confirmed_supply_date` stores this model attribute in the SQL database.
    confirmed_supply_date = db.Column(db.Date, nullable=True)
    # Database field: `expected_delivery_date` stores this model attribute in the SQL database.
    expected_delivery_date = db.Column(db.Date, nullable=True)
    # Database field: `total_price` stores this model attribute in the SQL database.
    total_price = db.Column(db.Float, nullable=False)
    # Database field: `note` stores this model attribute in the SQL database.
    note = db.Column(db.Text, nullable=True)
    # Database field: `status` stores this model attribute in the SQL database.
    status = db.Column(db.String(20), nullable=False, default=OFFER_PROPOSED)
    # Database field: `created_at` stores this model attribute in the SQL database.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    purchase_order = db.relationship('PurchaseOrder', back_populates='offers')
    offered_by = db.relationship('User')
