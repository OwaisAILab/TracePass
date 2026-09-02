from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, DateField, DateTimeField, IntegerField, FloatField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange

from app.models.supply_chain_event import EVENT_TYPES
from app.models.shipment import SHIPMENT_STATUSES
from app.models.lifecycle import LIFECYCLE_EVENT_TYPES


class ProductForm(FlaskForm):
    name = StringField("Product Name", validators=[DataRequired(), Length(max=150)])
    industry_id = SelectField("Industry", coerce=int, validators=[Optional()])
    category_id = SelectField("Product Category", coerce=int, validators=[DataRequired()])
    brand = StringField("Brand", validators=[Optional(), Length(max=100)])
    model = StringField("Model / SKU Model", validators=[Optional(), Length(max=100)])
    description = TextAreaField("Description", validators=[Optional()])
    sustainability_data = TextAreaField("Sustainability / Circularity Data", validators=[Optional()], render_kw={"placeholder": "e.g. recycled content, carbon footprint, repairability, recyclability"})
    manufacturer_org_id = SelectField("Manufacturer Organization", coerce=int, validators=[DataRequired()])
    image = FileField("Product Image", validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "webp", "avif"], "Images only: JPG, JPEG, PNG, WEBP, or AVIF.")])
    submit = SubmitField("Create Passport")


class BatchForm(FlaskForm):
    batch_no = StringField("Batch/Lot Number", validators=[DataRequired(), Length(max=100)])
    manufacture_date = DateField("Manufacture Date", validators=[Optional()])
    production_location = StringField("Production Location", validators=[Optional(), Length(max=150)])
    quantity = IntegerField("Quantity", validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField("Add Batch")


class MaterialLinkForm(FlaskForm):
    material_id = SelectField("Material", coerce=int, validators=[DataRequired()])
    supplier_id = SelectField("Supplier", coerce=int, validators=[Optional()])
    quantity = FloatField("Quantity", validators=[Optional(), NumberRange(min=0)])
    percentage = FloatField("Percentage (%)", validators=[Optional(), NumberRange(min=0, max=100)])
    submit = SubmitField("Link Material")


class EventForm(FlaskForm):
    batch_id = SelectField("Batch (optional)", coerce=int, validators=[Optional()])
    event_type = SelectField("Event Type", choices=[(t, t.replace("_", " ").title()) for t in EVENT_TYPES], validators=[DataRequired()])
    location = StringField("Location", validators=[Optional(), Length(max=150)])
    event_date = DateTimeField("Event Date/Time", format="%Y-%m-%dT%H:%M", validators=[DataRequired()], render_kw={"type": "datetime-local"})
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Log Event")


class ShipmentForm(FlaskForm):
    from_org_id = SelectField("From Organization", coerce=int, validators=[Optional()])
    to_org_id = SelectField("To Organization", coerce=int, validators=[Optional()])
    tracking_no = StringField("Tracking Number", validators=[Optional(), Length(max=100)])
    status = SelectField("Status", choices=[(s, s.replace("_", " ").title()) for s in SHIPMENT_STATUSES], validators=[DataRequired()])
    shipped_date = DateField("Shipped Date", validators=[Optional()])
    expected_delivery_date = DateField("Expected Delivery", validators=[Optional()])
    received_date = DateField("Received Date", validators=[Optional()])
    submit = SubmitField("Save Shipment")


class LifecycleEventForm(FlaskForm):
    event_type = SelectField("Lifecycle Event", choices=[(t, t.replace("_", " ").title()) for t in LIFECYCLE_EVENT_TYPES], validators=[DataRequired()])
    event_date = DateTimeField("Event Date/Time", format="%Y-%m-%dT%H:%M", validators=[DataRequired()], render_kw={"type": "datetime-local"})
    organization_id = SelectField("Organization", coerce=int, validators=[Optional()])
    location = StringField("Location", validators=[Optional(), Length(max=150)])
    notes = TextAreaField("Notes", validators=[Optional()])
    submit = SubmitField("Record Lifecycle Event")
