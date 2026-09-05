
from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField, FloatField, StringField, TextAreaField, SubmitField, DateField, BooleanField
from wtforms.validators import DataRequired, Optional, NumberRange, Length

from app.models.purchase_order import PO_STATUSES


# Defines the purchase order form class and groups its related data and behavior.
class PurchaseOrderForm(FlaskForm):
    product_id = SelectField("Product / Passport", coerce=int, validators=[DataRequired()])
    material_id = SelectField("Raw Material", coerce=int, validators=[Optional()])
    to_org_id = SelectField("Supplier", coerce=int, validators=[DataRequired()])
    quantity = IntegerField("Requested Quantity", validators=[DataRequired(), NumberRange(min=1)])
    requested_delivery_date = DateField("Required Delivery Date", validators=[Optional()])
    notes = TextAreaField("Buyer Notes", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Submit Purchase Order")


# Defines the purchase order response form class and groups its related data and behavior.
class PurchaseOrderResponseForm(FlaskForm):
    action = SelectField("Supplier Response", choices=[
        ("confirm", "Accept / Confirm"),
        ("reject", "Reject"),
    ], validators=[DataRequired()])
    confirmed_quantity = IntegerField("Confirmed Quantity", validators=[Optional(), NumberRange(min=1)])
    confirmed_supply_date = DateField("Confirmed Supply Date", validators=[Optional()])
    expected_delivery_date = DateField("Expected Delivery Date", validators=[Optional()])
    unit_price = FloatField("Proposed Unit Price (PKR)", validators=[Optional(), NumberRange(min=0)])
    supplier_notes = TextAreaField("Offer / Response Notes", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Send Response")


# Defines the purchase order status form class and groups its related data and behavior.
class PurchaseOrderStatusForm(FlaskForm):
    status = SelectField("Status", choices=[(s, s.replace("_", " ").title()) for s in PO_STATUSES], validators=[DataRequired()])
    submit = SubmitField("Update Status")


# Defines the shipment from poform class and groups its related data and behavior.
class ShipmentFromPOForm(FlaskForm):
    batch_id = SelectField("Manufacturing Batch (optional)", coerce=int, validators=[Optional()])
    tracking_no = TextAreaField("Tracking Number", validators=[Optional(), Length(max=100)])
    shipped_date = DateField("Dispatch Date", validators=[DataRequired()])
    expected_delivery_date = DateField("Expected Delivery", validators=[Optional()])
    submit = SubmitField("Dispatch Shipment")


# Defines the confirm receipt form class and groups its related data and behavior.
class ConfirmReceiptForm(FlaskForm):
    received_quantity = IntegerField("Received Quantity", validators=[DataRequired(), NumberRange(min=1)])
    received_date = DateField("Receipt Date", validators=[DataRequired()])
    notes = TextAreaField("Receipt Notes", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Confirm Receipt")


# Defines the supplier material form class and groups its related data and behavior.
class SupplierMaterialForm(FlaskForm):
    material_id = SelectField("Raw Material", coerce=int, validators=[DataRequired()])
    unit = StringField("Trading Unit", default="KG", validators=[DataRequired(), Length(max=30)])
    minimum_order_qty = FloatField("Minimum Order Quantity", validators=[Optional(), NumberRange(min=0)])
    lead_time_days = IntegerField("Typical Lead Time (days)", validators=[Optional(), NumberRange(min=0)])
    is_active = BooleanField("Currently Available", default=True)
    submit = SubmitField("Save Material Offering")


# Defines the purchase order offer form class and groups its related data and behavior.
class PurchaseOrderOfferForm(FlaskForm):
    unit_price = FloatField("Proposed Unit Price (PKR)", validators=[DataRequired(), NumberRange(min=0.01)])
    confirmed_supply_date = DateField("Proposed Supply Date", validators=[Optional()])
    expected_delivery_date = DateField("Expected Delivery Date", validators=[Optional()])
    note = TextAreaField("Negotiation Note", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Send Offer")
