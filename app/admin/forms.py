# TracePass code note: This module implements the app/admin/forms.py part of the application.
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SelectField, TextAreaField, FloatField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, Email, Length, NumberRange

from app.models.organization import ORG_TYPES


# Code explanation: Define the Organization Form data model or application component used by TracePass.
class OrganizationForm(FlaskForm):
    name = StringField("Organization Name", validators=[DataRequired(), Length(max=150)])
    type = SelectField("Type", choices=[(x, x.replace("_", " ").title()) for x in ORG_TYPES], validators=[DataRequired()])
    registration_no = StringField("Registration No.", validators=[Optional(), Length(max=100)])
    contact_email = StringField("Contact Email", validators=[Optional(), Email(), Length(max=120)])
    contact_phone = StringField("Contact Phone", validators=[Optional(), Length(max=30)])
    address = TextAreaField("Address", validators=[Optional()])
    submit = SubmitField("Save Organization")


# Code explanation: Define the Supplier Form data model or application component used by TracePass.
class SupplierForm(FlaskForm):
    organization_id = SelectField("Supplier Organization", coerce=int, validators=[DataRequired()])
    material_categories_supplied = StringField("Material Categories Supplied", validators=[Optional(), Length(max=255)])
    rating = FloatField("Rating (0–5)", validators=[Optional(), NumberRange(min=0, max=5)])
    submit = SubmitField("Save Supplier")


# Code explanation: Define the Material Form data model or application component used by TracePass.
class MaterialForm(FlaskForm):
    name = StringField("Material Name", validators=[DataRequired(), Length(max=150)])
    category = StringField("Material Category", validators=[Optional(), Length(max=100)])
    origin_country = StringField("Origin Country", validators=[Optional(), Length(max=100)])
    sustainability_notes = TextAreaField("Sustainability Notes", validators=[Optional()])
    submit = SubmitField("Save Material")


# Code explanation: Define the Product Category Form data model or application component used by TracePass.
class ProductCategoryForm(FlaskForm):
    name = StringField("Category Name", validators=[DataRequired(), Length(max=100)])
    description = TextAreaField("Description", validators=[Optional()])
    industry_id = SelectField("Industry", coerce=int, validators=[Optional()])
    parent_id = SelectField("Parent Category", coerce=int, validators=[Optional()])
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save Category")

# Code explanation: Define the Industry Form data model or application component used by TracePass.
class IndustryForm(FlaskForm):
    name = StringField("Industry Name", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField("Description", validators=[Optional()])
    image = FileField(
        "Industry Image",
        validators=[
            FileRequired("An industry image is required."),
            FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only: JPG, JPEG, PNG, or WEBP."),
        ],
    )
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save Industry")


# Code explanation: Define the Edit Industry Form data model or application component used by TracePass.
class EditIndustryForm(FlaskForm):
    name = StringField("Industry Name", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField("Description", validators=[Optional()])
    image = FileField(
        "Replace Industry Image",
        validators=[
            Optional(),
            FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only: JPG, JPEG, PNG, or WEBP."),
        ],
    )
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save Industry")

# Code explanation: Define the Product Template Form data model or application component used by TracePass.
class ProductTemplateForm(FlaskForm):
    name = StringField("Template Name", validators=[DataRequired(), Length(max=150)])
    industry_id = SelectField("Industry", coerce=int, validators=[DataRequired()])
    category_id = SelectField("Default Category", coerce=int, validators=[Optional()])
    description = TextAreaField("Description", validators=[Optional()])
    fields_definition = TextAreaField("Fields Definition", validators=[Optional()], description="One field per line: key|Label|type|required|help text")
    is_active = BooleanField("Active", default=True)
    submit = SubmitField("Save Template")
