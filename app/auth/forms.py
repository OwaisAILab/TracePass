# TracePass code note: This module implements the app/auth/forms.py part of the application.
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional

from app.models.user import User
from app.models.role import ALL_ROLES, ROLE_ADMIN, ROLE_CUSTOMER
from app.models.organization import Organization


# Code explanation: Custom WTForms validator that enforces TracePass password-strength requirements.
def _validate_password_strength(form, field):
    value = field.data or ""
    if len(value) < 8 or not any(c.isupper() for c in value) or not any(c.islower() for c in value) or not any(c.isdigit() for c in value):
        raise ValidationError("Password must be at least 8 characters and include uppercase, lowercase and a number.")


# Code explanation: Define the Login Form data model or application component used by TracePass.
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Log In")


# Code explanation: Define the Registration Form data model or application component used by TracePass.
class RegistrationForm(FlaskForm):
    """
    Public self-registration. Deliberately has NO role field — every
    self-registered account is a customer. Supplier/manufacturer/distributor/
    auditor/admin accounts represent real organizational identities and can
    only be created by an admin (see AdminCreateUserForm), who is responsible
    for verifying the person actually represents that organization. Letting
    people self-declare a supply-chain role would make the whole passport
    system trivially spoofable.
    """

    name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8), _validate_password_strength])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )
    submit = SubmitField("Register")

    # Code explanation: Implement the `validate email` operation used by this part of TracePass.
    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError("An account with this email already exists.")


# Code explanation: Define the Admin Create User Form data model or application component used by TracePass.
class AdminCreateUserForm(FlaskForm):
    """Admin-only. Creates accounts for organizational / staff roles.

    Customer accounts are created only via public self-registration so that
    end consumers are not mixed into admin-provisioned organizational identities.
    """

    name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    role = SelectField(
        "Role",
        choices=[(r, r.capitalize()) for r in ALL_ROLES if r != ROLE_CUSTOMER],
        validators=[DataRequired()],
    )
    organization_id = SelectField("Organization", coerce=int, validators=[Optional()])
    password = PasswordField("Temporary Password", validators=[DataRequired(), Length(min=8), _validate_password_strength])
    submit = SubmitField("Create User")

    # Code explanation: Implement the `validate email` operation used by this part of TracePass.
    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError("An account with this email already exists.")

    # Code explanation: Implement the `validate organization id` operation used by this part of TracePass.
    def validate_organization_id(self, field):
        # Organization is required for every role except customer/admin,
        # since a supplier/manufacturer/distributor/auditor account without
        # an org has no organizational identity to verify against.
        if self.role.data not in (ROLE_CUSTOMER, ROLE_ADMIN):
            if not field.data:
                raise ValidationError("An organization is required for this role.")

            org = Organization.query.get(field.data)
            if org is None:
                raise ValidationError("Selected organization does not exist.")
            if not org.is_verified:
                raise ValidationError(
                    f"'{org.name}' is not yet verified. Verify the organization "
                    "before creating accounts under it."
                )
