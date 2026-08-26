# TracePass code note: This module implements the app/models/order.py part of the application.
from datetime import datetime, timezone
from app.extensions import db

ORDER_PENDING = "pending"
ORDER_PAID = "paid"
ORDER_SHIPPED = "shipped"
ORDER_DELIVERED = "delivered"
ORDER_CANCELLED = "cancelled"
ORDER_STATUSES = [ORDER_PENDING, ORDER_PAID, ORDER_SHIPPED, ORDER_DELIVERED, ORDER_CANCELLED]


# Code explanation: Define the Order data model or application component used by TracePass.
class Order(db.Model):
    """
    A customer order. Checkout is a MOCK — there is no real payment
    processor here. order_number and a fake last-4 are stored purely so a
    customer has something concrete to quote when filing a return/complaint
    (see Complaint model). Never store full card numbers, even fake ones —
    the checkout form only ever collects a display-only last 4 digits.
    """

    __tablename__ = "orders"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `order_number` stores this model attribute in the SQL database.
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    # Database field: `customer_id` stores this model attribute in the SQL database.
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # Database field: `status` stores this model attribute in the SQL database.
    status = db.Column(db.String(20), default=ORDER_PAID, nullable=False)  # mock checkout "succeeds" immediately
    # Database field: `shipping_name` stores this model attribute in the SQL database.
    shipping_name = db.Column(db.String(150), nullable=True)
    # Database field: `shipping_address` stores this model attribute in the SQL database.
    shipping_address = db.Column(db.Text, nullable=True)
    # Database field: `payment_last4` stores this model attribute in the SQL database.
    payment_last4 = db.Column(db.String(4), nullable=True)  # display only, never a real card number
    # Database field: `total_amount` stores this model attribute in the SQL database.
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    # Database field: `created_at` stores this model attribute in the SQL database.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    customer = db.relationship("User")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<Order {self.order_number}>"


# Code explanation: Define the Order Item data model or application component used by TracePass.
class OrderItem(db.Model):
    __tablename__ = "order_items"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `order_id` stores this model attribute in the SQL database.
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    # Database field: `product_id` stores this model attribute in the SQL database.
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    # Database field: `quantity` stores this model attribute in the SQL database.
    quantity = db.Column(db.Integer, nullable=False)
    # Database field: `unit_price` stores this model attribute in the SQL database.
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)  # price AT time of purchase, not live product.price

    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<OrderItem product={self.product_id} qty={self.quantity}>"
