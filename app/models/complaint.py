# TracePass code note: This module implements the app/models/complaint.py part of the application.
from datetime import datetime, timezone
from app.extensions import db

COMPLAINT_TYPE_COMPLAINT = "complaint"
COMPLAINT_TYPE_RETURN = "return_request"
COMPLAINT_TYPES = [COMPLAINT_TYPE_COMPLAINT, COMPLAINT_TYPE_RETURN]

COMPLAINT_OPEN = "open"
COMPLAINT_INVESTIGATING = "investigating"
COMPLAINT_RESOLVED = "resolved"
COMPLAINT_STATUSES = [COMPLAINT_OPEN, COMPLAINT_INVESTIGATING, COMPLAINT_RESOLVED]


# Code explanation: Define the Complaint data model or application component used by TracePass.
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

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `product_id` stores this model attribute in the SQL database.
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    # Database field: `complaint_type` stores this model attribute in the SQL database.
    complaint_type = db.Column(db.String(20), nullable=False)  # complaint | return_request
    # Database field: `email` stores this model attribute in the SQL database.
    email = db.Column(db.String(120), nullable=False)
    # Database field: `description` stores this model attribute in the SQL database.
    description = db.Column(db.Text, nullable=False)
    # Database field: `order_reference` stores this model attribute in the SQL database.
    order_reference = db.Column(db.String(100), nullable=True)  # optional — retailer name, receipt #, order # if they have one
    # Database field: `status` stores this model attribute in the SQL database.
    status = db.Column(db.String(20), default=COMPLAINT_OPEN, nullable=False)
    # Database field: `created_at` stores this model attribute in the SQL database.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    # Database field: `resolved_at` stores this model attribute in the SQL database.
    resolved_at = db.Column(db.DateTime, nullable=True)
    # Database field: `resolution_notes` stores this model attribute in the SQL database.
    resolution_notes = db.Column(db.Text, nullable=True)

    product = db.relationship("Product", backref=db.backref("complaints", lazy="dynamic"))

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<Complaint {self.complaint_type} product={self.product_id}>"
