# TracePass code note: This module implements the app/models/compliance.py part of the application.
from datetime import datetime, timezone
from app.extensions import db

REQ_TYPE_CERTIFICATE = "certificate"
REQ_TYPE_DOCUMENT = "document"
REQUIREMENT_TYPES = [REQ_TYPE_CERTIFICATE, REQ_TYPE_DOCUMENT]

CHECK_PASS = "pass"
CHECK_FAIL = "fail"
CHECK_RESULTS = [CHECK_PASS, CHECK_FAIL]

REVIEW_APPROVED = "approved"
REVIEW_REJECTED = "rejected"
REVIEW_CORRECTIONS_REQUESTED = "corrections_requested"
REVIEW_DECISIONS = [REVIEW_APPROVED, REVIEW_REJECTED, REVIEW_CORRECTIONS_REQUESTED]


# Code explanation: Define the Compliance Rule data model or application component used by TracePass.
class ComplianceRule(db.Model):
    """
    A named policy, e.g. 'Apparel products must carry a Fair Trade certificate'.
    Scoped to a product category — category=None means it applies to every product.
    """

    __tablename__ = "compliance_rules"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `name` stores this model attribute in the SQL database.
    name = db.Column(db.String(150), nullable=False)
    # Database field: `category_id` stores this model attribute in the SQL database.
    category_id = db.Column(db.Integer, db.ForeignKey("product_categories.id"), nullable=True, index=True)  # None = all categories
    # Database field: `description` stores this model attribute in the SQL database.
    description = db.Column(db.Text, nullable=True)
    # Database field: `is_active` stores this model attribute in the SQL database.
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    # Database field: `created_at` stores this model attribute in the SQL database.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    category = db.relationship("ProductCategory", backref=db.backref("compliance_rules", lazy="dynamic"))
    requirements = db.relationship("ComplianceRequirement", back_populates="rule", cascade="all, delete-orphan")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<ComplianceRule {self.name}>"


# Code explanation: Define the Compliance Requirement data model or application component used by TracePass.
class ComplianceRequirement(db.Model):
    """
    A single checkable condition under a rule, e.g. 'must have a valid,
    non-expired certificate of type Fair Trade' or 'must have a test_report document'.
    """

    __tablename__ = "compliance_requirements"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `rule_id` stores this model attribute in the SQL database.
    rule_id = db.Column(db.Integer, db.ForeignKey("compliance_rules.id"), nullable=False)
    # Database field: `requirement_type` stores this model attribute in the SQL database.
    requirement_type = db.Column(db.String(20), nullable=False)  # certificate | document
    # Database field: `required_value` stores this model attribute in the SQL database.
    required_value = db.Column(db.String(150), nullable=False)  # cert_type or doc_type to match against
    # Database field: `is_mandatory` stores this model attribute in the SQL database.
    is_mandatory = db.Column(db.Boolean, default=True, nullable=False)
    # Database field: `description` stores this model attribute in the SQL database.
    description = db.Column(db.Text, nullable=True)

    rule = db.relationship("ComplianceRule", back_populates="requirements")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<ComplianceRequirement {self.requirement_type}:{self.required_value}>"


# Code explanation: Define the Compliance Check data model or application component used by TracePass.
class ComplianceCheck(db.Model):
    """
    Append-only record of a single requirement being evaluated against a product.
    NEVER update or delete a row here — re-running the engine writes NEW rows,
    so the full evaluation history is preserved for audit purposes.
    """

    __tablename__ = "compliance_checks"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `product_id` stores this model attribute in the SQL database.
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    # Database field: `rule_id` stores this model attribute in the SQL database.
    rule_id = db.Column(db.Integer, db.ForeignKey("compliance_rules.id"), nullable=False)
    # Database field: `requirement_id` stores this model attribute in the SQL database.
    requirement_id = db.Column(db.Integer, db.ForeignKey("compliance_requirements.id"), nullable=False)
    # Database field: `result` stores this model attribute in the SQL database.
    result = db.Column(db.String(10), nullable=False)  # pass | fail
    # Database field: `reason` stores this model attribute in the SQL database.
    reason = db.Column(db.Text, nullable=True)
    # Database field: `checked_at` stores this model attribute in the SQL database.
    checked_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    product = db.relationship("Product", backref=db.backref("compliance_checks", lazy="dynamic"))
    rule = db.relationship("ComplianceRule")
    requirement = db.relationship("ComplianceRequirement")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<ComplianceCheck product={self.product_id} {self.result}>"


# Code explanation: Define the Compliance Review data model or application component used by TracePass.
class ComplianceReview(db.Model):
    """
    An auditor/officer's decision on a product's compliance status. Also
    append-only — a new review is a new row, never an edit to a prior one,
    so the review history stays intact.
    """

    __tablename__ = "compliance_reviews"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `product_id` stores this model attribute in the SQL database.
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    # Database field: `reviewer_user_id` stores this model attribute in the SQL database.
    reviewer_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # Database field: `decision` stores this model attribute in the SQL database.
    decision = db.Column(db.String(30), nullable=False)  # approved | rejected | corrections_requested
    # Database field: `reasoning` stores this model attribute in the SQL database.
    reasoning = db.Column(db.Text, nullable=True)
    # Database field: `reviewed_at` stores this model attribute in the SQL database.
    reviewed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    product = db.relationship("Product", backref=db.backref("compliance_reviews", lazy="dynamic"))
    reviewer = db.relationship("User")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<ComplianceReview product={self.product_id} {self.decision}>"
