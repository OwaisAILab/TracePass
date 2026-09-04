# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
from datetime import datetime, timezone

from app.extensions import db


# What this code does: Defines the RegistrationRequestDocument class, grouping related data and behavior used by this part of the application.
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

    # What this code does: Implements the   repr   logic used by this part of the TracePass application.
    def __repr__(self):
        return f"<RegistrationRequestDocument {self.original_filename}>"
