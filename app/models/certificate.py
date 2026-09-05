
from datetime import datetime, timezone, date
from app.extensions import db


# Defines the certificate class and groups its related data and behavior.
class Certificate(db.Model):
    __tablename__ = "certificates"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)
    cert_type = db.Column(db.String(100), nullable=False)  # e.g. "ISO 14001", "Fair Trade", "REACH"
    issuing_body = db.Column(db.String(150), nullable=True)
    cert_number = db.Column(db.String(100), nullable=True)
    issue_date = db.Column(db.Date, nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    file_path = db.Column(db.String(255), nullable=True)  # stored evidence file, if uploaded
    uploaded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    review_status = db.Column(db.String(20), nullable=False, default="pending")  # pending | approved | rejected
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    product = db.relationship("Product")
    organization = db.relationship("Organization")
    uploaded_by = db.relationship("User", foreign_keys=[uploaded_by_user_id])
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_user_id])

    #  Checks a condition and returns a boolean result used by the application logic.
    def is_expired(self) -> bool:
        return self.expiry_date is not None and self.expiry_date < date.today()

# Implements the expires soon operation used by this module.
    def expires_soon(self, days: int = 30) -> bool:
        if self.expiry_date is None:
            return False
        delta = (self.expiry_date - date.today()).days
        return 0 <= delta <= days

# Provides the internal repr helper used by this module's workflow.
    def __repr__(self):
        return f"<Certificate {self.cert_type} #{self.cert_number}>"


# Defines the document class and groups its related data and behavior.
class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    certificate_id = db.Column(db.Integer, db.ForeignKey("certificates.id"), nullable=True)
    doc_type = db.Column(db.String(100), nullable=False)  # e.g. "test_report", "invoice", "declaration"
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    product = db.relationship("Product")
    certificate = db.relationship("Certificate", backref=db.backref("documents", lazy="dynamic"))
    uploaded_by = db.relationship("User")

# Provides the internal repr helper used by this module's workflow.
    def __repr__(self):
        return f"<Document {self.doc_type}>"
