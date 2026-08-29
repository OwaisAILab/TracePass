from datetime import datetime, timezone
from app.extensions import db

ORDER_PENDING = "pending"
ORDER_PAID = "paid"
ORDER_SHIPPED = "shipped"
ORDER_DELIVERED = "delivered"
ORDER_CANCELLED = "cancelled"
ORDER_STATUSES = [ORDER_PENDING, ORDER_PAID, ORDER_SHIPPED, ORDER_DELIVERED, ORDER_CANCELLED]


class Order(db.Model):
    """
    A customer order. Checkout is a MOCK — there is no real payment
    processor here. order_number and a fake last-4 are stored purely so a
    customer has something concrete to quote when filing a return/complaint
    (see Complaint model). Never store full card numbers, even fake ones —
    the checkout form only ever collects a display-only last 4 digits.
    """

    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), default=ORDER_PAID, nullable=False)  # mock checkout "succeeds" immediately
    shipping_name = db.Column(db.String(150), nullable=True)
    shipping_address = db.Column(db.Text, nullable=True)
    payment_last4 = db.Column(db.String(4), nullable=True)  # display only, never a real card number
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    customer = db.relationship("User")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order {self.order_number}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)  # price AT time of purchase, not live product.price

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product")

    def __repr__(self):
        return f"<OrderItem product={self.product_id} qty={self.quantity}>"
