# TracePass code note: This module implements the app/models/cart.py part of the application.
from datetime import datetime, timezone
from app.extensions import db


# Code explanation: Define the Cart data model or application component used by TracePass.
class Cart(db.Model):
    """One persistent cart per customer — created lazily on first add-to-cart."""

    __tablename__ = "carts"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `user_id` stores this model attribute in the SQL database.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    # Database field: `created_at` stores this model attribute in the SQL database.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", backref=db.backref("cart", uselist=False))
    items = db.relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

    # Code explanation: Implement the `total` operation used by this part of TracePass.
    def total(self):
        return sum((item.product.price or 0) * item.quantity for item in self.items)

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<Cart user={self.user_id}>"


# Code explanation: Define the Cart Item data model or application component used by TracePass.
class CartItem(db.Model):
    __tablename__ = "cart_items"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `cart_id` stores this model attribute in the SQL database.
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False)
    # Database field: `product_id` stores this model attribute in the SQL database.
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    # Database field: `quantity` stores this model attribute in the SQL database.
    quantity = db.Column(db.Integer, default=1, nullable=False)

    cart = db.relationship("Cart", back_populates="items")
    product = db.relationship("Product")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<CartItem product={self.product_id} qty={self.quantity}>"
