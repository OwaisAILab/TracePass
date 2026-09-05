
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SelectField, TextAreaField, FloatField, BooleanField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Optional, Email, Length, NumberRange, EqualTo, ValidationError

from app.models.organization import ORG_TYPES
from app.models.user import User


# Defines the organization form class and groups its related data and behavior.
class OrganizationForm(FlaskForm):
    name = StringField("Organization Name", validators=[DataRequired(), Length(max=150)])
    type = SelectField("Type", choices=[(x, x.replace("_", " ").title()) for x in ORG_TYPES], validators=[DataRequired()])
    registration_no = StringField("Registration No.", validators=[Optional(), Length(max=100)])
    contact_email = StringField("Contact Email", validators=[Optional(), Email(), Length(max=120)])
    contact_phone = StringField("Contact Phone", validators=[Optional(), Length(max=30)])
    address = TextAreaField("Address", validators=[Optional()])
    submit = SubmitField("Save Organization")


# Defines the supplier form class and groups its related data and behavior.
class SupplierForm(FlaskForm):
    organization_id = SelectField("Supplier Organization", coerce=int, validators=[DataRequired()])
    material_categories_supplied = StringField("Material Categories Supplied", validators=[Optional(), Length(max=255)])
    rating = FloatField("Rating (0–5)", validators=[Optional(), NumberRange(min=0, max=5)])
    submit = SubmitField("Save Supplier")


# Defines the material form class and groups its related data and behavior.
class MaterialForm(FlaskForm):
    name = StringField("Material Name", validators=[DataRequired(), Length(max=150)])
    category = StringField("Material Category", validators=[Optional(), Length(max=100)])
    origin_country = StringField("Origin Country", validators=[Optional(), Length(max=100)])
    sustainability_notes = TextAreaField("Sustainability Notes", validators=[Optional()])
    submit = SubmitField("Save Material")


# Defines the product category form class and groups its related data and behavior.
class ProductCategoryForm(FlaskForm):
    name = StringField("Category Name", validators=[DataRequired(), Length(max=100)])
    description = TextAreaField("Description", validators=[Optional()])
    industry_id = SelectField("Industry", coerce=int, validators=[Optional()])
    parent_id = SelectField("Parent Category", coerce=int, validators=[Optional()])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save Category")

# Defines the industry form class and groups its related data and behavior.
class IndustryForm(FlaskForm):
    name = StringField("Industry Name", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField("Description", validators=[Optional()])
    image = FileField(
        "Industry Image",
        validators=[
            FileRequired("An industry image is required."),
            FileAllowed(["jpg", "jpeg", "png", "webp", "avif"], "Images only: JPG, JPEG, PNG, WEBP, or AVIF."),
        ],
    )
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save Industry")


# Defines the edit industry form class and groups its related data and behavior.
class EditIndustryForm(FlaskForm):
    name = StringField("Industry Name", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField("Description", validators=[Optional()])
    image = FileField(
        "Replace Industry Image",
        validators=[
            Optional(),
            FileAllowed(["jpg", "jpeg", "png", "webp", "avif"], "Images only: JPG, JPEG, PNG, WEBP, or AVIF."),
        ],
    )
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save Industry")

# Defines the product template form class and groups its related data and behavior.
class ProductTemplateForm(FlaskForm):
    name = StringField("Template Name", validators=[DataRequired(), Length(max=150)])
    industry_id = SelectField("Industry", coerce=int, validators=[DataRequired()])
    category_id = SelectField("Default Category", coerce=int, validators=[Optional()])
    description = TextAreaField("Description", validators=[Optional()])
    fields_definition = TextAreaField("Fields Definition", validators=[Optional()], description="One field per line: key|Label|type|required|help text")
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save Template")

#  Checks whether request password strength satisfies the project rules before processing continues.
def _validate_request_password_strength(form, field):
    """Require a strong password for the account that will be created after approval."""
    value = field.data or ""
    if (not any(c.isupper() for c in value) or
            not any(c.islower() for c in value) or
            not any(c.isdigit() for c in value)):
        raise ValidationError("Password must include uppercase, lowercase and a number.")


# Defines the registration request form class and groups its related data and behavior.
class RegistrationRequestForm(FlaskForm):
    """Public form used to request a non-customer organizational account."""

    name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Applicant Email", validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField("Applicant Phone", validators=[Optional(), Length(max=30)])
    requested_role = SelectField(
        "Requested Role",
        choices=[
            ("manufacturer", "Manufacturer"),
            ("supplier", "Supplier"),
            ("distributor", "Distributor"),
            ("retailer", "Retailer"),
            ("auditor", "Auditor"),
        ],
        validators=[DataRequired()],
    )
    organization_name = StringField("Organization Name", validators=[DataRequired(), Length(max=150)])
    registration_no = StringField("Registration / License No.", validators=[Optional(), Length(max=100)])
    organization_email = StringField("Organization Email", validators=[Optional(), Email(), Length(max=120)])
    organization_phone = StringField("Organization Phone", validators=[Optional(), Length(max=30)])
    address = TextAreaField("Organization Address", validators=[Optional()])
    password = PasswordField("Requested Password", validators=[DataRequired(), Length(min=8), _validate_request_password_strength])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    reason = TextAreaField("Reason for joining TracePass", validators=[Optional()])
    authenticity_documents = FileField(
        "Authenticity / Registration Documents",
        validators=[FileRequired("At least one authenticity document is required."), FileAllowed(["pdf", "png", "jpg", "jpeg", "avif", "docx", "xlsx"], "PDF, image, DOCX or XLSX only.")],
        description="Upload at least one official registration, license, tax, certification or other authenticity document. You may select multiple files.",
    )
    submit = SubmitField("Submit Account Request")

    #  Checks whether email satisfies the project rules before processing continues.
    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError("An account with this email already exists. Please use Login instead.")
