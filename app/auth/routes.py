
import secrets
from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models.user import User
from app.models.role import Role, ROLE_CUSTOMER
from app.auth.forms import LoginForm, RegistrationForm, EmailOTPForm
from app.models.email_verification import EmailVerification
from app.services.email import send_email

auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")


# Provides the internal create otp challenge helper used by this module.
def _create_otp_challenge(email, purpose, payload, file_paths=None):
    """Create a short-lived hashed OTP challenge and email the code."""
    # Remove previous active challenge for this email/purpose.
    EmailVerification.query.filter_by(
        email=email, purpose=purpose, verified_at=None
    ).delete(synchronize_session=False)

    code = f"{secrets.randbelow(1_000_000):06d}"
    challenge = EmailVerification(
        email=email,
        purpose=purpose,
        otp_hash=generate_password_hash(code),
        payload=payload,
        file_paths=file_paths,
        expires_at=datetime.now(timezone.utc) + timedelta(
            minutes=current_app.config["EMAIL_OTP_EXPIRY_MINUTES"]
        ),
    )
    db.session.add(challenge)
    db.session.commit()

    try:
        send_email(
            email,
            "TracePass email verification OTP",
            (
                f"Your TracePass verification code is {code}.\n\n"
                f"This code expires in {current_app.config['EMAIL_OTP_EXPIRY_MINUTES']} minutes. "
                "Do not share this code with anyone."
            ),
            (
                f"<h2>TracePass Email Verification</h2>"
                f"<p>Your verification code is:</p>"
                f"<p style='font-size:28px;font-weight:700;letter-spacing:8px'>{code}</p>"
                f"<p>This code expires in {current_app.config['EMAIL_OTP_EXPIRY_MINUTES']} minutes.</p>"
                "<p>If you did not request this, you can safely ignore this email.</p>"
            ),
        )
    except Exception:
        db.session.delete(challenge)
        db.session.commit()
        raise

    session["email_verification_id"] = challenge.id
    session["email_verification_purpose"] = purpose
    return challenge


# Provides the internal pending challenge helper used by this module's workflow.
def _pending_challenge(expected_purpose):
    challenge_id = session.get("email_verification_id")
    if not challenge_id or session.get("email_verification_purpose") != expected_purpose:
        return None
    challenge = db.session.get(EmailVerification, challenge_id)
    if not challenge or challenge.verified_at or challenge.is_expired():
        return None
    return challenge


#  Processes account registration data and creates a new user after validation.
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        customer_role = Role.query.filter_by(name=ROLE_CUSTOMER).first()
        if customer_role is None:
            flash("Registration is temporarily unavailable. Contact an administrator.", "danger")
            return render_template("auth/register.html", form=form)

        payload = {
            "name": form.name.data.strip(),
            "email": email,
            "password_hash": generate_password_hash(form.password.data),
            "role_id": customer_role.id,
        }
        try:
            _create_otp_challenge(email, "customer_registration", payload)
        except Exception as exc:
            current_app.logger.exception("Customer registration OTP email failed")
            flash("We could not send the verification email. Please try again later.", "danger")
            return render_template("auth/register.html", form=form)

        flash("A 6-digit OTP has been sent to your email address.", "info")
        return redirect(url_for("auth.verify_email"))

    return render_template("auth/register.html", form=form)


# Handles the Flask route /verify-email by validating input and running the verify email workflow.
@auth_bp.route("/verify-email", methods=["GET", "POST"])
def verify_email():
    purpose = session.get("email_verification_purpose")
    if purpose not in {"customer_registration", "organization_registration"}:
        flash("No active email verification was found. Please start registration again.", "warning")
        return redirect(url_for("auth.register"))

    challenge = _pending_challenge(purpose)
    if not challenge:
        session.pop("email_verification_id", None)
        session.pop("email_verification_purpose", None)
        target = url_for("main.contact") if purpose == "organization_registration" else url_for("auth.register")
        flash("Your email verification session has expired. Please submit the registration again.", "warning")
        return redirect(target)

    form = EmailOTPForm()
    if form.validate_on_submit():
        if challenge.attempts >= current_app.config["EMAIL_OTP_MAX_ATTEMPTS"]:
            flash("Too many incorrect OTP attempts. Please request a new code.", "danger")
            return render_template("auth/verify_email.html", form=form, email=challenge.email)

        from werkzeug.security import check_password_hash
        challenge.attempts += 1
        if challenge.is_expired() or not check_password_hash(challenge.otp_hash, form.otp.data.strip()):
            db.session.commit()
            flash("Invalid or expired OTP.", "danger")
            return render_template("auth/verify_email.html", form=form, email=challenge.email)

        payload = challenge.payload

        if purpose == "customer_registration":
            if User.query.filter_by(email=challenge.email).first():
                db.session.delete(challenge)
                db.session.commit()
                session.pop("email_verification_id", None)
                session.pop("email_verification_purpose", None)
                flash("An account with this email already exists. Please sign in.", "warning")
                return redirect(url_for("auth.login"))

            user = User(
                name=payload["name"],
                email=payload["email"],
                password_hash=payload["password_hash"],
                role_id=payload["role_id"],
            )
            db.session.add(user)
            flash("Email verified and customer account created. You can now log in.", "success")
            db.session.delete(challenge)
            db.session.commit()
            session.pop("email_verification_id", None)
            session.pop("email_verification_purpose", None)
            return redirect(url_for("auth.login"))

        # Organizational applicants are only forwarded to administrators
        # after their email ownership has been proven.
        from app.models.registration_request_document import RegistrationRequestDocument
        from app.models.notification import Notification
        from app.models.role import ROLE_ADMIN, Role
        from app.models.registration_request import RegistrationRequest, REQUEST_PENDING

        duplicate_user = User.query.filter_by(email=challenge.email).first()
        duplicate_request = RegistrationRequest.query.filter_by(
            email=challenge.email, status=REQUEST_PENDING
        ).first()
        if duplicate_user or duplicate_request:
            flash("An account or pending request already exists for this email.", "warning")
            db.session.delete(challenge)
            db.session.commit()
            session.pop("email_verification_id", None)
            session.pop("email_verification_purpose", None)
            return redirect(url_for("main.index"))

        item = RegistrationRequest(
            name=payload["name"],
            email=payload["email"],
            phone=payload.get("phone"),
            requested_role=payload["requested_role"],
            organization_name=payload["organization_name"],
            registration_no=payload.get("registration_no"),
            organization_type=payload["organization_type"],
            organization_email=payload.get("organization_email"),
            organization_phone=payload.get("organization_phone"),
            address=payload.get("address"),
            reason=payload.get("reason"),
            password_hash=payload["password_hash"],
            status=REQUEST_PENDING,
        )
        db.session.add(item)
        db.session.flush()

        # Move the verified applicant's temporary evidence into the permanent
        # request folder and create the document records.
        import os
        import shutil
        upload_root = current_app.config["UPLOAD_FOLDER"]
        for entry in (challenge.file_paths or []):
            source = os.path.join(upload_root, entry["path"])
            target_dir = os.path.join(upload_root, "registration_requests", str(item.id))
            os.makedirs(target_dir, exist_ok=True)
            target_name = os.path.basename(source)
            target = os.path.join(target_dir, target_name)
            if os.path.exists(source):
                shutil.move(source, target)
                db.session.add(RegistrationRequestDocument(
                    registration_request_id=item.id,
                    document_type="authenticity_evidence",
                    original_filename=entry["original_filename"],
                    file_path=os.path.relpath(target, upload_root).replace(os.sep, "/"),
                ))

        admin_role = Role.query.filter_by(name=ROLE_ADMIN).first()
        if admin_role:
            for admin in User.query.filter_by(role_id=admin_role.id, is_active=True).all():
                db.session.add(Notification(
                    user_id=admin.id,
                    notif_type="account_request",
                    message=f"New verified {item.requested_role} account request from {item.name} ({item.organization_name}).",
                ))

        challenge.verified_at = datetime.now(timezone.utc)
        db.session.delete(challenge)
        db.session.commit()
        session.pop("email_verification_id", None)
        session.pop("email_verification_purpose", None)
        flash("Email verified. Your organizational registration request has been forwarded to the administrator for review.", "success")
        return redirect(url_for("main.index"))

    return render_template("auth/verify_email.html", form=form, email=challenge.email)


# Handles the Flask route /verify-email/resend by validating input and running the resend email otp workflow.
@auth_bp.route("/verify-email/resend", methods=["POST"])
def resend_email_otp():
    purpose = session.get("email_verification_purpose")
    if purpose not in {"customer_registration", "organization_registration"}:
        flash("Your verification session has expired. Please register again.", "warning")
        return redirect(url_for("auth.register"))

    challenge = _pending_challenge(purpose)
    if not challenge:
        flash("Your verification session has expired. Please register again.", "warning")
        target = url_for("main.contact") if purpose == "organization_registration" else url_for("auth.register")
        return redirect(target)

    try:
        _create_otp_challenge(
            challenge.email, purpose, challenge.payload, challenge.file_paths
        )
    except Exception:
        current_app.logger.exception("OTP resend failed")
        flash("We could not send a new verification email.", "danger")
        return redirect(url_for("auth.verify_email"))

    flash("A new OTP has been sent to your email.", "info")
    return redirect(url_for("auth.verify_email"))


#  Handles user authentication by validating credentials and creating a secure logged-in session.
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form=form)
        if not user.is_active:
            flash("This account has been deactivated. Contact an administrator.", "danger")
            return render_template("auth/login.html", form=form)
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or not next_page.startswith("/"):
            next_page = url_for("main.dashboard")
        return redirect(next_page)
    return render_template("auth/login.html", form=form)


#  Ends the current user session and redirects the user away from protected pages.
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))
