# TracePass code note: This module implements the app/compliance/routes.py part of the application.
import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.decorators import role_required
from app.models.role import ROLE_ADMIN, ROLE_MANUFACTURER, ROLE_AUDITOR
from app.models.product import Product
from app.models.certificate import Certificate, Document
from app.models.compliance import ComplianceRule, ComplianceRequirement, ComplianceReview
from app.compliance.forms import CertificateForm, CertificateReviewForm, DocumentForm, ComplianceRuleForm, ComplianceRequirementForm, ReviewForm
from app.compliance.engine import evaluate_product_compliance
from app.uploads import validate_upload

compliance_bp = Blueprint("compliance", __name__, template_folder="../templates/compliance")

CAN_MANAGE_EVIDENCE = (ROLE_ADMIN, ROLE_MANUFACTURER)
CAN_REVIEW = (ROLE_ADMIN, ROLE_AUDITOR)
# Auditors don't upload evidence, but they must be able to open it during review.
CAN_VIEW_EVIDENCE = (ROLE_ADMIN, ROLE_MANUFACTURER, ROLE_AUDITOR)


# Code explanation: Implement the `save upload` operation used by this part of TracePass.
def _save_upload(file_storage):
    """Saves an uploaded file with a random-prefixed safe filename, returns the relative path."""
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = secure_filename(file_storage.filename)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    filepath = os.path.join(upload_dir, unique_name)
    file_storage.save(filepath)
    return unique_name


# --- certificates -----------------------------------------------------------

# Code explanation: Implement the `add certificate` operation used by this part of TracePass.
@compliance_bp.route("/products/<int:product_id>/certificates", methods=["POST"])
@login_required
@role_required(*CAN_MANAGE_EVIDENCE)
def add_certificate(product_id):
    product = Product.query.get_or_404(product_id)
    form = CertificateForm()

    if form.validate_on_submit():
        file_path = None
        if form.file.data:
            validate_upload(form.file.data, {"pdf", "png", "jpg", "jpeg"})
            file_path = _save_upload(form.file.data)

        cert = Certificate(
            product_id=product.id if form.scope.data == "product" else None,
            organization_id=product.manufacturer_org_id if form.scope.data == "organization" else None,
            cert_type=form.cert_type.data.strip(),
            issuing_body=form.issuing_body.data.strip() if form.issuing_body.data else None,
            cert_number=form.cert_number.data.strip() if form.cert_number.data else None,
            issue_date=form.issue_date.data,
            expiry_date=form.expiry_date.data,
            file_path=file_path,
            uploaded_by_user_id=current_user.id,
            review_status="pending",
        )
        db.session.add(cert)
        db.session.commit()
        flash(f"Certificate '{cert.cert_type}' added.", "success")
    else:
        for field, errors in form.errors.items():
            for err in errors:
                flash(f"{field}: {err}", "danger")

    return redirect(url_for("tracepass.view_product", product_id=product.id))


# --- documents ---------------------------------------------------------------

# Code explanation: Implement the `add document` operation used by this part of TracePass.
@compliance_bp.route("/products/<int:product_id>/documents", methods=["POST"])
@login_required
@role_required(*CAN_MANAGE_EVIDENCE)
def add_document(product_id):
    product = Product.query.get_or_404(product_id)
    form = DocumentForm()

    if form.validate_on_submit():
        validate_upload(form.file.data, {"pdf", "png", "jpg", "jpeg", "docx", "xlsx"})
        file_path = _save_upload(form.file.data)
        doc = Document(
            product_id=product.id,
            doc_type=form.doc_type.data.strip(),
            file_path=file_path,
            uploaded_by_user_id=current_user.id,
        )
        db.session.add(doc)
        db.session.commit()
        flash(f"Document '{doc.doc_type}' uploaded.", "success")
    else:
        for field, errors in form.errors.items():
            for err in errors:
                flash(f"{field}: {err}", "danger")

    return redirect(url_for("tracepass.view_product", product_id=product.id))


# --- evidence download --------------------------------------------------------
# Certificates and documents are uploaded but were never retrievable — there was
# no way for a manufacturer to double check what they filed, or for an auditor
# to open the evidence they are supposed to be reviewing (spec section 11).

# Code explanation: Implement the `download certificate` operation used by this part of TracePass.
@compliance_bp.route("/certificates/<int:cert_id>/file")
@login_required
@role_required(*CAN_VIEW_EVIDENCE)
def download_certificate(cert_id):
    cert = Certificate.query.get_or_404(cert_id)
    if not cert.file_path:
        abort(404)
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(upload_dir, cert.file_path, as_attachment=True)


# Code explanation: Implement the `download document` operation used by this part of TracePass.
@compliance_bp.route("/documents/<int:doc_id>/file")
@login_required
@role_required(*CAN_VIEW_EVIDENCE)
def download_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(upload_dir, doc.file_path, as_attachment=True)


# --- certificate evidence review ---------------------------------------------

# Code explanation: Implement the `review certificate` operation used by this part of TracePass.
@compliance_bp.route("/certificates/<int:cert_id>/review", methods=["POST"])
@login_required
@role_required(*CAN_REVIEW)
def review_certificate(cert_id):
    cert = Certificate.query.get_or_404(cert_id)
    form = CertificateReviewForm()
    if form.validate_on_submit():
        cert.review_status = form.decision.data
        cert.reviewed_by_user_id = current_user.id
        cert.reviewed_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        cert.review_comments = form.comments.data.strip() if form.comments.data else None
        db.session.commit()
        affected_products = []
        if cert.product_id:
            product = Product.query.get(cert.product_id)
            if product:
                affected_products.append(product)
        elif cert.organization_id:
            affected_products = Product.query.filter_by(manufacturer_org_id=cert.organization_id).all()
        for product in affected_products:
            evaluate_product_compliance(product)
        flash(f"Certificate evidence {form.decision.data} and compliance was re-evaluated for {len(affected_products)} product(s).", "success")
    else:
        for field, errors in form.errors.items():
            for err in errors:
                flash(f"{field}: {err}", "danger")
    return redirect(url_for("tracepass.view_product", product_id=cert.product_id)) if cert.product_id else redirect(url_for("reporting.dashboard"))


# --- rule engine trigger ------------------------------------------------------

# Code explanation: Evaluate a product against configured compliance rules and persist the result.
@compliance_bp.route("/products/<int:product_id>/run-check", methods=["POST"])
@login_required
@role_required(ROLE_ADMIN, ROLE_MANUFACTURER, ROLE_AUDITOR)
def run_compliance_check(product_id):
    product = Product.query.get_or_404(product_id)
    summary = evaluate_product_compliance(product)

    if summary["rules_checked"] == 0:
        flash("No active compliance rules apply to this product's category yet.", "warning")
    else:
        flash(
            f"Compliance check complete: {summary['passed']} passed, {summary['failed']} failed "
            f"({summary['mandatory_failed']} mandatory). Status: {summary['resulting_status']}.",
            "success" if summary["resulting_status"] == "compliant" else "warning",
        )
    return redirect(url_for("tracepass.view_product", product_id=product.id))


# --- officer review ------------------------------------------------------------

# Code explanation: Implement the `submit review` operation used by this part of TracePass.
@compliance_bp.route("/products/<int:product_id>/reviews", methods=["POST"])
@login_required
@role_required(*CAN_REVIEW)
def submit_review(product_id):
    product = Product.query.get_or_404(product_id)
    form = ReviewForm()

    if form.validate_on_submit():
        review = ComplianceReview(
            product_id=product.id,
            reviewer_user_id=current_user.id,
            decision=form.decision.data,
            reasoning=form.reasoning.data,
        )
        db.session.add(review)

        # A review is a human override layered on top of the automated engine.
        # Approved -> compliant; rejected -> non_compliant; corrections
        # requested leaves the door open (treated as non_compliant until
        # re-submitted and re-checked).
        from app.models.product import COMPLIANCE_COMPLIANT, COMPLIANCE_NON_COMPLIANT

        if form.decision.data == "approved":
            product.compliance_status = COMPLIANCE_COMPLIANT
        else:
            product.compliance_status = COMPLIANCE_NON_COMPLIANT

        db.session.commit()
        flash(f"Review recorded: {form.decision.data.replace('_', ' ')}.", "success")
    else:
        for field, errors in form.errors.items():
            for err in errors:
                flash(f"{field}: {err}", "danger")

    return redirect(url_for("tracepass.view_product", product_id=product.id))


# --- rule & requirement management (admin only) -------------------------------

# Code explanation: Implement the `list rules` operation used by this part of TracePass.
@compliance_bp.route("/admin/compliance-rules")
@login_required
@role_required(ROLE_ADMIN)
def list_rules():
    rules = ComplianceRule.query.order_by(ComplianceRule.created_at.desc()).all()
    return render_template("compliance/rules.html", rules=rules)


# Code explanation: Implement the `new rule` operation used by this part of TracePass.
@compliance_bp.route("/admin/compliance-rules/new", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def new_rule():
    form = ComplianceRuleForm()
    from app.models.product_category import ProductCategory
    form.category_id.choices = [(0, "— All categories —")] + [(c.id, c.name) for c in ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.name).all()]
    if form.validate_on_submit():
        rule = ComplianceRule(
            name=form.name.data.strip(),
            category_id=form.category_id.data or None,
            description=form.description.data,
            is_active=form.is_active.data,
        )
        db.session.add(rule)
        db.session.commit()
        flash(f"Rule '{rule.name}' created. Now add requirements to it.", "success")
        return redirect(url_for("compliance.view_rule", rule_id=rule.id))
    return render_template("compliance/rule_form.html", form=form)


# Code explanation: Implement the `view rule` operation used by this part of TracePass.
@compliance_bp.route("/admin/compliance-rules/<int:rule_id>")
@login_required
@role_required(ROLE_ADMIN)
def view_rule(rule_id):
    rule = ComplianceRule.query.get_or_404(rule_id)
    req_form = ComplianceRequirementForm()
    return render_template("compliance/rule_detail.html", rule=rule, req_form=req_form)


# Code explanation: Implement the `add requirement` operation used by this part of TracePass.
@compliance_bp.route("/admin/compliance-rules/<int:rule_id>/requirements", methods=["POST"])
@login_required
@role_required(ROLE_ADMIN)
def add_requirement(rule_id):
    rule = ComplianceRule.query.get_or_404(rule_id)
    form = ComplianceRequirementForm()
    if form.validate_on_submit():
        req = ComplianceRequirement(
            rule_id=rule.id,
            requirement_type=form.requirement_type.data,
            required_value=form.required_value.data.strip(),
            is_mandatory=form.is_mandatory.data,
            description=form.description.data,
        )
        db.session.add(req)
        db.session.commit()
        flash("Requirement added.", "success")
    else:
        for field, errors in form.errors.items():
            for err in errors:
                flash(f"{field}: {err}", "danger")
    return redirect(url_for("compliance.view_rule", rule_id=rule.id))
