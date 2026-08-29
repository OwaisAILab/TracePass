from datetime import datetime, timezone
from app.extensions import db


class Cart(db.Model):
    """One persistent cart per customer — created lazily on first add-to-cart."""

    __tablename__ = "carts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", backref=db.backref("cart", uselist=False))
    items = db.relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

    def total(self):
        return sum((item.product.price or 0) * item.quantity for item in self.items)

    def __repr__(self):
        return f"<Cart user={self.user_id}>"


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    cart = db.relationship("Cart", back_populates="items")
    product = db.relationship("Product")

    def __repr__(self):
        return f"<CartItem product={self.product_id} qty={self.quantity}>"
