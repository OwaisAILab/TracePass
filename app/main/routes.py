from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models.industry import Industry
from app.models.registration_request import RegistrationRequest, REQUEST_PENDING, REQUESTABLE_ROLES
from app.admin.forms import RegistrationRequestForm
from app.extensions import db

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    industries = Industry.query.filter_by(is_active=True).order_by(Industry.name).all()
    return render_template("main/landing.html", industries=industries)


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    """Public Contact Us page where organizational users request access.

    The request does not create an account immediately. It creates a pending
    record for an administrator to verify and approve.
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegistrationRequestForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        # Prevent duplicate pending requests for the same applicant.
        duplicate = RegistrationRequest.query.filter_by(email=email, status=REQUEST_PENDING).first()
        if duplicate:
            flash("A registration request for this email is already awaiting administrator review.", "warning")
            return redirect(url_for("main.contact"))

        item = RegistrationRequest(
            name=form.name.data.strip(),
            email=email,
            phone=form.phone.data.strip() if form.phone.data else None,
            requested_role=form.requested_role.data,
            organization_name=form.organization_name.data.strip(),
            registration_no=form.registration_no.data.strip() if form.registration_no.data else None,
            organization_type=form.requested_role.data,
            organization_email=form.organization_email.data.strip().lower() if form.organization_email.data else None,
            organization_phone=form.organization_phone.data.strip() if form.organization_phone.data else None,
            address=form.address.data.strip() if form.address.data else None,
            reason=form.reason.data.strip() if form.reason.data else None,
            status=REQUEST_PENDING,
        )
        item.set_password(form.password.data)
        db.session.add(item)
        db.session.flush()

        # Notify every active administrator so the request is visible in the
        # existing TracePass notification center without requiring email.
        from app.models.user import User
        from app.models.notification import Notification
        from app.models.role import ROLE_ADMIN
        admin_role_ids = [r.id for r in __import__("app.models.role", fromlist=["Role"]).Role.query.filter_by(name=ROLE_ADMIN).all()]
        for admin in User.query.filter(User.role_id.in_(admin_role_ids), User.is_active.is_(True)).all():
            db.session.add(Notification(
                user_id=admin.id,
                notif_type="account_request",
                message=f"New {item.requested_role} account request from {item.name} ({item.organization_name}).",
            ))
        db.session.commit()
        flash("Your account request has been submitted. An administrator will review and verify your organization.", "success")
        return redirect(url_for("main.index"))

    return render_template("main/contact.html", form=form)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    return redirect(url_for("reporting.dashboard"))
