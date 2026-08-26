# TracePass code note: This module implements the app/models/organization.py part of the application.
from datetime import datetime, timezone
from app.extensions import db

ORG_TYPE_SUPPLIER = "supplier"
ORG_TYPE_MANUFACTURER = "manufacturer"
ORG_TYPE_DISTRIBUTOR = "distributor"
ORG_TYPE_RETAILER = "retailer"
ORG_TYPE_AUDITOR = "auditor"

ORG_TYPES = [ORG_TYPE_SUPPLIER, ORG_TYPE_MANUFACTURER, ORG_TYPE_DISTRIBUTOR, ORG_TYPE_RETAILER, ORG_TYPE_AUDITOR]


# Code explanation: Define the Organization data model or application component used by TracePass.
class Organization(db.Model):
    __tablename__ = "organizations"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `name` stores this model attribute in the SQL database.
    name = db.Column(db.String(150), nullable=False)
    # Database field: `type` stores this model attribute in the SQL database.
    type = db.Column(db.String(30), nullable=False)  # one of ORG_TYPES
    # Database field: `registration_no` stores this model attribute in the SQL database.
    registration_no = db.Column(db.String(100), unique=True, nullable=True)
    # Database field: `contact_email` stores this model attribute in the SQL database.
    contact_email = db.Column(db.String(120), nullable=True)
    # Database field: `contact_phone` stores this model attribute in the SQL database.
    contact_phone = db.Column(db.String(30), nullable=True)
    # Database field: `address` stores this model attribute in the SQL database.
    address = db.Column(db.Text, nullable=True)
    # Database field: `is_verified` stores this model attribute in the SQL database.
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    # Database field: `created_at` stores this model attribute in the SQL database.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    users = db.relationship("User", back_populates="organization", lazy="dynamic")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<Organization {self.name} ({self.type})>"
