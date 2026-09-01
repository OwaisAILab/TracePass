from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import uuid

from app.models.industry import Industry
from app.models.registration_request import RegistrationRequest, REQUEST_PENDING, REQUESTABLE_ROLES
from app.admin.forms import RegistrationRequestForm
from app.models.registration_request_document import RegistrationRequestDocument
from app.uploads import validate_upload
from app.extensions import db
from app.models.product import Product, STATUS_PUBLISHED
from app.models.organization import Organization
from app.models.verification import VerificationLog

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Public landing page.

    Loads the active industries for the industry showcase grid, and computes
    a handful of live platform counters (published products, organizations,
    verification events, industries) so the landing page can show real
    numbers instead of hardcoded marketing figures.
    """
    industries = Industry.query.filter_by(is_active=True).order_by(Industry.name).all()
    stats = {
        "products": Product.query.filter_by(status=STATUS_PUBLISHED).count(),        # only published passports count as "live"
        "organizations": Organization.query.count(),                                  # total organizations on the network
        "verifications": VerificationLog.query.count(),                               # total verification scans ever logged
        "industries": len(industries),                                                # number of active industries shown above
    }
    return render_template("main/landing.html", industries=industries, stats=stats)


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

        # Authenticity evidence is mandatory. The form displays a multi-file
        # input, while Flask exposes the submitted files through getlist().
        files = [f for f in request.files.getlist("authenticity_documents") if f and f.filename]
        if not files:
            db.session.rollback()
            form.authenticity_documents.errors.append("At least one authenticity document is required.")
            return render_template("main/contact.html", form=form)

        document_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "registration_requests", str(item.id))
        os.makedirs(document_dir, exist_ok=True)
        allowed = {"pdf", "png", "jpg", "jpeg", "avif", "docx", "xlsx"}
        for uploaded in files:
            validate_upload(uploaded, allowed)
            original = secure_filename(uploaded.filename) or "authenticity_document"
            ext = os.path.splitext(original)[1].lower()
            stored_name = f"{uuid.uuid4().hex}{ext}"
            stored_path = os.path.join(document_dir, stored_name)
            uploaded.save(stored_path)
            db.session.add(RegistrationRequestDocument(
                registration_request_id=item.id,
                document_type="authenticity_evidence",
                original_filename=original,
                file_path=os.path.relpath(stored_path, current_app.config["UPLOAD_FOLDER"]).replace(os.sep, "/"),
            ))

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
