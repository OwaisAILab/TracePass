# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
from flask import Blueprint
from app.extensions import csrf

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')
csrf.exempt(api_bp)

from app.api import routes  # noqa: E402,F401
