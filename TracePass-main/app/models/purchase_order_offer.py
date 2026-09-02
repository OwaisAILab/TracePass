from datetime import datetime, timezone
from app.extensions import db

OFFER_PROPOSED = 'proposed'
OFFER_ACCEPTED = 'accepted'
OFFER_REJECTED = 'rejected'
OFFER_SUPERSEDED = 'superseded'

class PurchaseOrderOffer(db.Model):
    __tablename__ = 'purchase_order_offers'

    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    offered_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False, default='PKR')
    quantity = db.Column(db.Integer, nullable=False)
    confirmed_supply_date = db.Column(db.Date, nullable=True)
    expected_delivery_date = db.Column(db.Date, nullable=True)
    total_price = db.Column(db.Float, nullable=False)
    note = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default=OFFER_PROPOSED)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    purchase_order = db.relationship('PurchaseOrder', back_populates='offers')
    offered_by = db.relationship('User')
