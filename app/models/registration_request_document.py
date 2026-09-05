
from datetime import datetime, timezone

from app.extensions import db


# Defines the registration request document class and groups its related data and behavior.
class RegistrationRequestDocument(db.Model):
    """Authenticity evidence submitted with a public account request."""

    __tablename__ = "registration_request_documents"

    id = db.Column(db.Integer, primary_key=True)
    registration_request_id = db.Column(db.Integer, db.ForeignKey("registration_requests.id"), nullable=False, index=True)
    document_type = db.Column(db.String(100), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    registration_request = db.relationship(
        "RegistrationRequest",
        back_populates="authenticity_documents",
    )

# Provides the internal repr helper used by this module's workflow.
    def __repr__(self):
        return f"<RegistrationRequestDocument {self.original_filename}>"
