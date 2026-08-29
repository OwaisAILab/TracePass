from datetime import datetime, timezone

from werkzeug.security import generate_password_hash

from app.extensions import db


# Only organizational roles may enter the approval workflow. Customers use
# the existing public self-registration flow instead.
REQUESTABLE_ROLES = (
    "supplier",
    "manufacturer",
    "distributor",
    "retailer",
    "auditor",
)

REQUEST_PENDING = "pending"
REQUEST_APPROVED = "approved"
REQUEST_REJECTED = "rejected"
REQUEST_STATUSES = (REQUEST_PENDING, REQUEST_APPROVED, REQUEST_REJECTED)


class RegistrationRequest(db.Model):
    """Public request for a controlled TracePass organizational account.

    The applicant submits the request without receiving access immediately.
    The password is stored only as a hash; the account is created after an
    administrator approves the request.
    """

    __tablename__ = "registration_requests"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=True)
    requested_role = db.Column(db.String(30), nullable=False)
    organization_name = db.Column(db.String(150), nullable=False)
    registration_no = db.Column(db.String(100), nullable=True)
    organization_type = db.Column(db.String(30), nullable=False)
    organization_email = db.Column(db.String(120), nullable=True)
    organization_phone = db.Column(db.String(30), nullable=True)
    address = db.Column(db.Text, nullable=True)
    reason = db.Column(db.Text, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=REQUEST_PENDING, index=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])
    created_user = db.relationship("User", foreign_keys=[created_user_id])
    organization = db.relationship("Organization", foreign_keys=[organization_id])

    def set_password(self, password: str) -> None:
        """Hash the requested password; never store the plaintext password."""
        self.password_hash = generate_password_hash(password)

    def __repr__(self):
        return f"<RegistrationRequest {self.email} ({self.status})>"
