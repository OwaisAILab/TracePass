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


class ComplianceRule(db.Model):
    """
    A named policy, e.g. 'Apparel products must carry a Fair Trade certificate'.
    Scoped to a product category — category=None means it applies to every product.
    """

    __tablename__ = "compliance_rules"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("product_categories.id"), nullable=True, index=True)  # None = all categories
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    category = db.relationship("ProductCategory", backref=db.backref("compliance_rules", lazy="dynamic"))
    requirements = db.relationship("ComplianceRequirement", back_populates="rule", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ComplianceRule {self.name}>"


class ComplianceRequirement(db.Model):
    """
    A single checkable condition under a rule, e.g. 'must have a valid,
    non-expired certificate of type Fair Trade' or 'must have a test_report document'.
    """

    __tablename__ = "compliance_requirements"

    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey("compliance_rules.id"), nullable=False)
    requirement_type = db.Column(db.String(20), nullable=False)  # certificate | document
    required_value = db.Column(db.String(150), nullable=False)  # cert_type or doc_type to match against
    is_mandatory = db.Column(db.Boolean, default=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    rule = db.relationship("ComplianceRule", back_populates="requirements")

    def __repr__(self):
        return f"<ComplianceRequirement {self.requirement_type}:{self.required_value}>"


class ComplianceCheck(db.Model):
    """
    Append-only record of a single requirement being evaluated against a product.
    NEVER update or delete a row here — re-running the engine writes NEW rows,
    so the full evaluation history is preserved for audit purposes.
    """

    __tablename__ = "compliance_checks"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    rule_id = db.Column(db.Integer, db.ForeignKey("compliance_rules.id"), nullable=False)
    requirement_id = db.Column(db.Integer, db.ForeignKey("compliance_requirements.id"), nullable=False)
    result = db.Column(db.String(10), nullable=False)  # pass | fail
    reason = db.Column(db.Text, nullable=True)
    checked_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    product = db.relationship("Product", backref=db.backref("compliance_checks", lazy="dynamic"))
    rule = db.relationship("ComplianceRule")
    requirement = db.relationship("ComplianceRequirement")

    def __repr__(self):
        return f"<ComplianceCheck product={self.product_id} {self.result}>"


class ComplianceReview(db.Model):
    """
    An auditor/officer's decision on a product's compliance status. Also
    append-only — a new review is a new row, never an edit to a prior one,
    so the review history stays intact.
    """

    __tablename__ = "compliance_reviews"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    reviewer_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    decision = db.Column(db.String(30), nullable=False)  # approved | rejected | corrections_requested
    reasoning = db.Column(db.Text, nullable=True)
    reviewed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    product = db.relationship("Product", backref=db.backref("compliance_reviews", lazy="dynamic"))
    reviewer = db.relationship("User")

    def __repr__(self):
        return f"<ComplianceReview product={self.product_id} {self.decision}>"
