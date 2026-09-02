from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DateField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, Length

from app.models.compliance import REQUIREMENT_TYPES, REVIEW_DECISIONS


class CertificateForm(FlaskForm):
    cert_type = StringField("Certificate Type", validators=[DataRequired(), Length(max=100)])
    issuing_body = StringField("Issuing Body", validators=[Optional(), Length(max=150)])
    cert_number = StringField("Certificate Number", validators=[Optional(), Length(max=100)])
    issue_date = DateField("Issue Date", validators=[Optional()])
    expiry_date = DateField("Expiry Date", validators=[Optional()])
    scope = SelectField("Applies To", choices=[("product", "This product only"), ("organization", "Whole organization")])
    file = FileField("Certificate Evidence File", validators=[DataRequired(), FileAllowed(["pdf", "png", "jpg", "jpeg", "avif"], "PDF or image only")])
    submit = SubmitField("Add Certificate")


class CertificateReviewForm(FlaskForm):
    decision = SelectField("Decision", choices=[("approved", "Approve evidence"), ("rejected", "Reject evidence")], validators=[DataRequired()])
    comments = TextAreaField("Review Comments", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Record Certificate Review")


class DocumentForm(FlaskForm):
    doc_type = StringField("Document Type", validators=[DataRequired(), Length(max=100)])
    file = FileField("File", validators=[DataRequired(), FileAllowed(["pdf", "png", "jpg", "jpeg", "avif", "docx", "xlsx"], "Unsupported file type")])
    submit = SubmitField("Upload Document")


class ComplianceRuleForm(FlaskForm):
    name = StringField("Rule Name", validators=[DataRequired(), Length(max=150)])
    category_id = SelectField("Applies to Category", coerce=int, validators=[Optional()])
    description = TextAreaField("Description", validators=[Optional()])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Create Rule")


class ComplianceRequirementForm(FlaskForm):
    requirement_type = SelectField("Type", choices=[(t, t.capitalize()) for t in REQUIREMENT_TYPES], validators=[DataRequired()])
    required_value = StringField("Required Value (cert type or document type)", validators=[DataRequired(), Length(max=150)])
    is_mandatory = BooleanField("Mandatory", default=True)
    description = TextAreaField("Description", validators=[Optional()])
    submit = SubmitField("Add Requirement")


class ReviewForm(FlaskForm):
    decision = SelectField("Decision", choices=[(d, d.replace("_", " ").title()) for d in REVIEW_DECISIONS], validators=[DataRequired()])
    reasoning = TextAreaField("Reasoning", validators=[Optional()])
    submit = SubmitField("Submit Review")
