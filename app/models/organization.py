# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
from datetime import datetime, timezone
from app.extensions import db

ORG_TYPE_SUPPLIER = "supplier"
ORG_TYPE_MANUFACTURER = "manufacturer"
ORG_TYPE_DISTRIBUTOR = "distributor"
ORG_TYPE_RETAILER = "retailer"
ORG_TYPE_AUDITOR = "auditor"

ORG_TYPES = [ORG_TYPE_SUPPLIER, ORG_TYPE_MANUFACTURER, ORG_TYPE_DISTRIBUTOR, ORG_TYPE_RETAILER, ORG_TYPE_AUDITOR]


# What this code does: Defines the Organization class, grouping related data and behavior used by this part of the application.
class Organization(db.Model):
    __tablename__ = "organizations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(30), nullable=False)  # one of ORG_TYPES
    registration_no = db.Column(db.String(100), unique=True, nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    contact_phone = db.Column(db.String(30), nullable=True)
    address = db.Column(db.Text, nullable=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    users = db.relationship("User", back_populates="organization", lazy="dynamic")

    # What this code does: Implements the   repr   logic used by this part of the TracePass application.
    def __repr__(self):
        return f"<Organization {self.name} ({self.type})>"
