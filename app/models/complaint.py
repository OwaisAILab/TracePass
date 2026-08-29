from datetime import datetime, timezone
from app.extensions import db

COMPLAINT_TYPE_COMPLAINT = "complaint"
COMPLAINT_TYPE_RETURN = "return_request"
COMPLAINT_TYPES = [COMPLAINT_TYPE_COMPLAINT, COMPLAINT_TYPE_RETURN]

COMPLAINT_OPEN = "open"
COMPLAINT_INVESTIGATING = "investigating"
COMPLAINT_RESOLVED = "resolved"
COMPLAINT_STATUSES = [COMPLAINT_OPEN, COMPLAINT_INVESTIGATING, COMPLAINT_RESOLVED]


class Complaint(db.Model):
    """
    Public-facing complaint/return request, submitted from the QR passport
    page with NO login and NO proof of purchase required — just an email
    address. This is intentionally open (by product decision, not an
    oversight): a customer who bought from a retailer/reseller may have no
    TracePass account and no order number to quote, and requiring one would
    block legitimate complaints from exactly the people most likely to have
    them. The trade-off is that this channel accepts unverified reports —
    it's a triage inbox, not proof of purchase. Anything downstream (an
    actual refund, replacement, etc.) still requires the retailer or
    manufacturer to separately verify the claim before acting on it.
    """

    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    complaint_type = db.Column(db.String(20), nullable=False)  # complaint | return_request
    email = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    order_reference = db.Column(db.String(100), nullable=True)  # optional — retailer name, receipt #, order # if they have one
    status = db.Column(db.String(20), default=COMPLAINT_OPEN, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)

    product = db.relationship("Product", backref=db.backref("complaints", lazy="dynamic"))

    def __repr__(self):
        return f"<Complaint {self.complaint_type} product={self.product_id}>"
