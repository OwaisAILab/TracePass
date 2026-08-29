from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, Email, NumberRange, Regexp

from app.models.complaint import COMPLAINT_TYPES


class AddToCartForm(FlaskForm):
    quantity = IntegerField("Quantity", default=1, validators=[DataRequired(), NumberRange(min=1, max=20)])
    submit = SubmitField("Add to Cart")


class CheckoutForm(FlaskForm):
    """
    Mock checkout — there is no real payment processor. card_number is
    intentionally NOT collected in full; only a display last-4 is stored,
    and even that is never validated as a real card. This form exists to
    make the flow feel complete for a demo, not to process real payments.
    """

    shipping_name = StringField("Full Name", validators=[DataRequired(), Length(max=150)])
    shipping_address = TextAreaField("Shipping Address", validators=[DataRequired()])
    card_last4 = StringField(
        "Card Number (demo only — enter any 4 digits)",
        validators=[DataRequired(), Regexp(r"^\d{4}$", message="Enter exactly 4 digits — this is a mock checkout, not a real card field.")],
    )
    submit = SubmitField("Place Order (Mock Payment)")


class ComplaintForm(FlaskForm):
    complaint_type = SelectField("Request Type", choices=[(t, t.replace("_", " ").title()) for t in COMPLAINT_TYPES], validators=[DataRequired()])
    email = StringField("Your Email", validators=[DataRequired(), Email(), Length(max=120)])
    order_reference = StringField("Order # / Retailer Name (optional)", validators=[Optional(), Length(max=100)])
    description = TextAreaField("Tell us what happened", validators=[DataRequired()])
    submit = SubmitField("Submit Request")
