
from datetime import datetime, timezone

from app.extensions import db


# Defines the email verification class and groups its related data and behavior.
class EmailVerification(db.Model):
    """One-time email verification challenge used before registration is accepted.

    The pending registration data is kept server-side until the applicant proves
    control of the supplied email address. OTP values are stored only as hashes.
    """

    __tablename__ = "email_verifications"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    purpose = db.Column(db.String(40), nullable=False, index=True)
    otp_hash = db.Column(db.String(255), nullable=False)
    payload = db.Column(db.JSON, nullable=False)
    file_paths = db.Column(db.JSON, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    verified_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    #  Checks a condition and returns a boolean result used by the application logic.
    def is_expired(self):
        now = datetime.now(timezone.utc)
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return expires <= now
