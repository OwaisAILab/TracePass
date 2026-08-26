# TracePass code note: This module implements the app/main/routes.py part of the application.
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required

from app.models.industry import Industry

main_bp = Blueprint("main", __name__)


# Code explanation: Render the public TracePass landing page and its dynamic industry cards.
@main_bp.route("/")
def index():
    industries = Industry.query.filter_by(is_active=True).order_by(Industry.name).all()
    return render_template("main/landing.html", industries=industries)


# Code explanation: Build the authenticated reporting/dashboard view from current system data.
@main_bp.route("/dashboard")
@login_required
def dashboard():
    return redirect(url_for("reporting.dashboard"))
