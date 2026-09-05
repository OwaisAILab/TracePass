
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import uuid
import json

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


# Handles the Flask route / by validating input and running the index workflow.
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
    # Serialize industries for the landing page's Industries showcase grid, so it
    # reflects real admin-managed data (name, description, bundled/uploaded image)
    # instead of hardcoded marketing content.
    industries_json = json.dumps([
        {
            "name": industry.name,
            "description": industry.description,
            "image_url": industry.image_url,
        }
        for industry in industries
    ])
    return render_template(
        "main/landing.html", industries=industries, stats=stats, industries_json=industries_json
    )


# Handles the Flask route /contact by validating input and running the contact workflow.
@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    """Public organizational registration request with mandatory email OTP.

    The applicant's email is verified first. Only after successful OTP
    verification is the request stored and forwarded to administrators.
    """
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegistrationRequestForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        duplicate = RegistrationRequest.query.filter_by(
            email=email, status=REQUEST_PENDING
        ).first()
        if duplicate:
            flash("A registration request for this email is already awaiting administrator review.", "warning")
            return redirect(url_for("main.contact"))

        # Validate and save authenticity evidence to a temporary server-side
        # location before sending the OTP. Files never need to pass through
        # the browser/session while the applicant is verifying the email.
        files = [f for f in request.files.getlist("authenticity_documents") if f and f.filename]
        if not files:
            form.authenticity_documents.errors.append("At least one authenticity document is required.")
            return render_template("main/contact.html", form=form)

        temp_id = uuid.uuid4().hex
        document_dir = os.path.join(
            current_app.config["UPLOAD_FOLDER"], "registration_pending", temp_id
        )
        os.makedirs(document_dir, exist_ok=True)
        file_paths = []

        try:
            allowed = {"pdf", "png", "jpg", "jpeg", "avif", "docx", "xlsx"}
            for uploaded in files:
                validate_upload(uploaded, allowed)
                original = secure_filename(uploaded.filename) or "authenticity_document"
                ext = os.path.splitext(original)[1].lower()
                stored_name = f"{uuid.uuid4().hex}{ext}"
                stored_path = os.path.join(document_dir, stored_name)
                uploaded.save(stored_path)
                file_paths.append({
                    "path": os.path.relpath(
                        stored_path, current_app.config["UPLOAD_FOLDER"]
                    ).replace(os.sep, "/"),
                    "original_filename": original,
                })
        except Exception:
            import shutil
            shutil.rmtree(document_dir, ignore_errors=True)
            raise

        item_payload = {
            "name": form.name.data.strip(),
            "email": email,
            "phone": form.phone.data.strip() if form.phone.data else None,
            "requested_role": form.requested_role.data,
            "organization_name": form.organization_name.data.strip(),
            "registration_no": form.registration_no.data.strip() if form.registration_no.data else None,
            "organization_type": form.requested_role.data,
            "organization_email": form.organization_email.data.strip().lower() if form.organization_email.data else None,
            "organization_phone": form.organization_phone.data.strip() if form.organization_phone.data else None,
            "address": form.address.data.strip() if form.address.data else None,
            "reason": form.reason.data.strip() if form.reason.data else None,
            "password_hash": __import__("werkzeug.security", fromlist=["generate_password_hash"]).generate_password_hash(form.password.data),
        }

        from app.auth.routes import _create_otp_challenge
        try:
            _create_otp_challenge(
                email, "organization_registration",
                item_payload, file_paths=file_paths
            )
        except Exception:
            import shutil
            shutil.rmtree(document_dir, ignore_errors=True)
            current_app.logger.exception("Organizational registration OTP email failed")
            flash("We could not send the verification email. Please check the email address and try again.", "danger")
            return render_template("main/contact.html", form=form)

        flash("A 6-digit OTP has been sent to your applicant email. Verify it to forward your request to the administrator.", "info")
        return redirect(url_for("auth.verify_email"))

    return render_template("main/contact.html", form=form)


# Handles the Flask route /dashboard by validating input and running the dashboard workflow.
@main_bp.route("/dashboard")
@login_required
def dashboard():
    return redirect(url_for("reporting.dashboard"))
