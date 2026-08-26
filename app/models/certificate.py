# TracePass code note: This module implements the app/models/certificate.py part of the application.
from datetime import datetime, timezone, date
from app.extensions import db


# Code explanation: Define the Certificate data model or application component used by TracePass.
class Certificate(db.Model):
    __tablename__ = "certificates"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `product_id` stores this model attribute in the SQL database.
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    # Database field: `organization_id` stores this model attribute in the SQL database.
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)
    # Database field: `cert_type` stores this model attribute in the SQL database.
    cert_type = db.Column(db.String(100), nullable=False)  # e.g. "ISO 14001", "Fair Trade", "REACH"
    # Database field: `issuing_body` stores this model attribute in the SQL database.
    issuing_body = db.Column(db.String(150), nullable=True)
    # Database field: `cert_number` stores this model attribute in the SQL database.
    cert_number = db.Column(db.String(100), nullable=True)
    # Database field: `issue_date` stores this model attribute in the SQL database.
    issue_date = db.Column(db.Date, nullable=True)
    # Database field: `expiry_date` stores this model attribute in the SQL database.
    expiry_date = db.Column(db.Date, nullable=True)
    # Database field: `file_path` stores this model attribute in the SQL database.
    file_path = db.Column(db.String(255), nullable=True)  # stored evidence file, if uploaded
    # Database field: `uploaded_by_user_id` stores this model attribute in the SQL database.
    uploaded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    # Database field: `review_status` stores this model attribute in the SQL database.
    review_status = db.Column(db.String(20), nullable=False, default="pending")  # pending | approved | rejected
    # Database field: `reviewed_by_user_id` stores this model attribute in the SQL database.
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    # Database field: `reviewed_at` stores this model attribute in the SQL database.
    reviewed_at = db.Column(db.DateTime, nullable=True)
    # Database field: `review_comments` stores this model attribute in the SQL database.
    review_comments = db.Column(db.Text, nullable=True)
    # Database field: `created_at` stores this model attribute in the SQL database.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    product = db.relationship("Product")
    organization = db.relationship("Organization")
    uploaded_by = db.relationship("User", foreign_keys=[uploaded_by_user_id])
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_user_id])

    # Code explanation: Implement the `is expired` operation used by this part of TracePass.
    def is_expired(self) -> bool:
        return self.expiry_date is not None and self.expiry_date < date.today()

    # Code explanation: Implement the `expires soon` operation used by this part of TracePass.
    def expires_soon(self, days: int = 30) -> bool:
        if self.expiry_date is None:
            return False
        delta = (self.expiry_date - date.today()).days
        return 0 <= delta <= days

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<Certificate {self.cert_type} #{self.cert_number}>"


# Code explanation: Define the Document data model or application component used by TracePass.
class Document(db.Model):
    __tablename__ = "documents"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `product_id` stores this model attribute in the SQL database.
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    # Database field: `certificate_id` stores this model attribute in the SQL database.
    certificate_id = db.Column(db.Integer, db.ForeignKey("certificates.id"), nullable=True)
    # Database field: `doc_type` stores this model attribute in the SQL database.
    doc_type = db.Column(db.String(100), nullable=False)  # e.g. "test_report", "invoice", "declaration"
    # Database field: `file_path` stores this model attribute in the SQL database.
    file_path = db.Column(db.String(255), nullable=False)
    # Database field: `uploaded_by_user_id` stores this model attribute in the SQL database.
    uploaded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    # Database field: `uploaded_at` stores this model attribute in the SQL database.
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    product = db.relationship("Product")
    certificate = db.relationship("Certificate", backref=db.backref("documents", lazy="dynamic"))
    uploaded_by = db.relationship("User")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<Document {self.doc_type}>"
