
from datetime import datetime, timezone
from app.extensions import db

NOTIF_CERT_EXPIRING = "cert_expiring"
NOTIF_CHECK_FAILED = "check_failed"
NOTIF_REVIEW_PENDING = "review_pending"
NOTIF_RECALL_ISSUED = "recall_issued"
NOTIF_PO_UPDATE = "purchase_order_update"
NOTIF_TYPES = [NOTIF_CERT_EXPIRING, NOTIF_CHECK_FAILED, NOTIF_REVIEW_PENDING, NOTIF_RECALL_ISSUED, NOTIF_PO_UPDATE]


# Defines the notification class and groups its related data and behavior.
class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    notif_type = db.Column(db.String(30), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship("User", backref=db.backref("notifications", lazy="dynamic"))
    product = db.relationship("Product")

# Provides the internal repr helper used by this module's workflow.
    def __repr__(self):
        return f"<Notification {self.notif_type} user={self.user_id}>"
