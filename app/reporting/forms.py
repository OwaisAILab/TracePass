
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, Length

from app.models.recall_incident import RECALL_STATUSES, INCIDENT_STATUSES


# Defines the recall form class and groups its related data and behavior.
class RecallForm(FlaskForm):
    batch_id = SelectField("Batch (optional — leave blank to recall entire product)", coerce=int, validators=[Optional()])
    reason = TextAreaField("Reason for Recall", validators=[DataRequired()])
    submit = SubmitField("Issue Recall")


# Defines the recall status form class and groups its related data and behavior.
class RecallStatusForm(FlaskForm):
    status = SelectField("Status", choices=[(s, s.replace("_", " ").title()) for s in RECALL_STATUSES], validators=[DataRequired()])
    submit = SubmitField("Update Status")


# Defines the incident form class and groups its related data and behavior.
class IncidentForm(FlaskForm):
    description = TextAreaField("Incident Description", validators=[DataRequired()])
    submit = SubmitField("Report Incident")


# Defines the incident status form class and groups its related data and behavior.
class IncidentStatusForm(FlaskForm):
    status = SelectField("Status", choices=[(s, s.replace("_", " ").title()) for s in INCIDENT_STATUSES], validators=[DataRequired()])
    resolution_notes = TextAreaField("Resolution Notes", validators=[Optional()])
    submit = SubmitField("Update Status")
