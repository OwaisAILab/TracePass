
from datetime import datetime, timezone, timedelta
from app.extensions import db

OTP_PURPOSE_CUSTOMER_REGISTRATION = "customer_registration"
OTP_PURPOSE_ORG_REQUEST = "org_registration_request"


# Defines the email otp class and groups its related data and behavior.
class EmailOTP(db.Model):
    """Stores temporary one-time passwords generated for email validation."""

    __tablename__ = "email_otps"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    otp_code = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.String(50), nullable=False, index=True)
    payload = db.Column(db.Text, nullable=True)  # JSON-encoded payload (e.g. name, password_hash)
    request_id = db.Column(db.Integer, db.ForeignKey("registration_requests.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    attempts = db.Column(db.Integer, default=0, nullable=False)

    registration_request = db.relationship("RegistrationRequest", foreign_keys=[request_id])

    #  Checks a condition and returns a boolean result used by the application logic.
    @property
    def is_expired(self) -> bool:
        now = datetime.now(timezone.utc)
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return now > exp

# Provides the internal repr helper used by this module's workflow.
    def __repr__(self):
        return f"<EmailOTP {self.email} ({self.purpose}) {'used' if self.is_used else 'active'}>"
