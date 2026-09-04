# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, Length

from app.models.recall_incident import RECALL_STATUSES, INCIDENT_STATUSES


# What this code does: Defines the RecallForm class, grouping related data and behavior used by this part of the application.
class RecallForm(FlaskForm):
    batch_id = SelectField("Batch (optional — leave blank to recall entire product)", coerce=int, validators=[Optional()])
    reason = TextAreaField("Reason for Recall", validators=[DataRequired()])
    submit = SubmitField("Issue Recall")


# What this code does: Defines the RecallStatusForm class, grouping related data and behavior used by this part of the application.
class RecallStatusForm(FlaskForm):
    status = SelectField("Status", choices=[(s, s.replace("_", " ").title()) for s in RECALL_STATUSES], validators=[DataRequired()])
    submit = SubmitField("Update Status")


# What this code does: Defines the IncidentForm class, grouping related data and behavior used by this part of the application.
class IncidentForm(FlaskForm):
    description = TextAreaField("Incident Description", validators=[DataRequired()])
    submit = SubmitField("Report Incident")


# What this code does: Defines the IncidentStatusForm class, grouping related data and behavior used by this part of the application.
class IncidentStatusForm(FlaskForm):
    status = SelectField("Status", choices=[(s, s.replace("_", " ").title()) for s in INCIDENT_STATUSES], validators=[DataRequired()])
    resolution_notes = TextAreaField("Resolution Notes", validators=[Optional()])
    submit = SubmitField("Update Status")
