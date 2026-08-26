# TracePass code note: This module implements the app/models/notification.py part of the application.
from datetime import datetime, timezone
from app.extensions import db

NOTIF_CERT_EXPIRING = "cert_expiring"
NOTIF_CHECK_FAILED = "check_failed"
NOTIF_REVIEW_PENDING = "review_pending"
NOTIF_RECALL_ISSUED = "recall_issued"
NOTIF_PO_UPDATE = "purchase_order_update"
NOTIF_TYPES = [NOTIF_CERT_EXPIRING, NOTIF_CHECK_FAILED, NOTIF_REVIEW_PENDING, NOTIF_RECALL_ISSUED, NOTIF_PO_UPDATE]


# Code explanation: Define the Notification data model or application component used by TracePass.
class Notification(db.Model):
    __tablename__ = "notifications"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `user_id` stores this model attribute in the SQL database.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # Database field: `notif_type` stores this model attribute in the SQL database.
    notif_type = db.Column(db.String(30), nullable=False)
    # Database field: `message` stores this model attribute in the SQL database.
    message = db.Column(db.String(255), nullable=False)
    # Database field: `product_id` stores this model attribute in the SQL database.
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    # Database field: `is_read` stores this model attribute in the SQL database.
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    # Database field: `created_at` stores this model attribute in the SQL database.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship("User", backref=db.backref("notifications", lazy="dynamic"))
    product = db.relationship("Product")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<Notification {self.notif_type} user={self.user_id}>"
