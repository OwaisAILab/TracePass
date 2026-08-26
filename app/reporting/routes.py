# TracePass code note: This module implements the app/reporting/routes.py part of the application.
import os
import csv
from io import StringIO
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app, Response
from flask_login import login_required, current_user

from app.extensions import db
from app.decorators import role_required
from app.models.role import ROLE_ADMIN, ROLE_MANUFACTURER, ROLE_AUDITOR
from app.models.product import Product
from app.models.certificate import Certificate
from app.models.compliance import ComplianceCheck, ComplianceReview
from app.models.recall_incident import Recall, Incident
from app.models.audit_log import AuditLog
from app.models.notification import Notification
from app.reporting.forms import RecallForm, RecallStatusForm, IncidentForm, IncidentStatusForm
from app.reporting.notifications import generate_notifications_for_user
from app.reporting.kpis import compute_kpis
from app.reporting.pdf_report import build_compliance_report_pdf

reporting_bp = Blueprint("reporting", __name__, template_folder="../templates/reporting")

CAN_MANAGE_EVIDENCE = (ROLE_ADMIN, ROLE_MANUFACTURER)
CAN_REVIEW = (ROLE_ADMIN, ROLE_AUDITOR)


# --- dashboard --------------------------------------------------------------

# Code explanation: Build the authenticated reporting/dashboard view from current system data.
@reporting_bp.route("/reports/dashboard")
@login_required
def dashboard():
    generate_notifications_for_user(current_user)

    scope_org_id = current_user.organization_id if current_user.has_role(ROLE_MANUFACTURER) else None
    kpis = compute_kpis(scope_org_id=scope_org_id)

    notifications = (
        Notification.query.filter_by(user_id=current_user.id, is_read=False)
        .order_by(Notification.created_at.desc())
        .limit(10)
        .all()
    )

    recent_recalls_query = Recall.query.join(Product)
    recent_incidents_query = Incident.query.join(Product)
    if scope_org_id is not None:
        recent_recalls_query = recent_recalls_query.filter(Product.manufacturer_org_id == scope_org_id)
        recent_incidents_query = recent_incidents_query.filter(Product.manufacturer_org_id == scope_org_id)
    recent_recalls = recent_recalls_query.order_by(Recall.issued_at.desc()).limit(5).all()
    recent_incidents = recent_incidents_query.order_by(Incident.reported_at.desc()).limit(5).all()

    return render_template(
        "reporting/dashboard.html",
        kpis=kpis,
        notifications=notifications,
        recent_recalls=recent_recalls,
        recent_incidents=recent_incidents,
    )


# --- notifications -----------------------------------------------------------

# Code explanation: Implement the `mark notification read` operation used by this part of TracePass.
@reporting_bp.route("/notifications/<int:notif_id>/read", methods=["POST"])
@login_required
def mark_notification_read(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != current_user.id:
        return redirect(url_for("reporting.dashboard"))
    notif.is_read = True
    db.session.commit()
    return redirect(url_for("reporting.dashboard"))


# --- notification center -------------------------------------------------------

# Code explanation: Implement the `notifications` operation used by this part of TracePass.
@reporting_bp.route("/notifications")
@login_required
def notifications():
    generate_notifications_for_user(current_user)
    page = request.args.get("page", 1, type=int)
    pagination = (Notification.query.filter_by(user_id=current_user.id)
                  .order_by(Notification.created_at.desc())
                  .paginate(page=page, per_page=20, error_out=False))
    return render_template("reporting/notifications.html", pagination=pagination, notifications=pagination.items)


# Code explanation: Implement the `mark all notifications read` operation used by this part of TracePass.
@reporting_bp.route("/notifications/read-all", methods=["POST"])
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True}, synchronize_session=False)
    db.session.commit()
    flash("All notifications marked as read.", "success")
    return redirect(url_for("reporting.notifications"))


# --- recalls -------------------------------------------------------------------

# Code explanation: Implement the `issue recall` operation used by this part of TracePass.
@reporting_bp.route("/products/<int:product_id>/recalls", methods=["POST"])
@login_required
@role_required(*CAN_MANAGE_EVIDENCE)
def issue_recall(product_id):
    product = Product.query.get_or_404(product_id)
    form = RecallForm()
    form.batch_id.choices = [(0, "— Entire product —")] + [(b.id, b.batch_no) for b in product.batches]

    if form.validate_on_submit():
        recall = Recall(
            product_id=product.id,
            batch_id=form.batch_id.data if form.batch_id.data else None,
            reason=form.reason.data,
            issued_by_user_id=current_user.id,
        )
        db.session.add(recall)
        db.session.commit()
        flash("Recall issued.", "danger")
    else:
        for field, errors in form.errors.items():
            for err in errors:
                flash(f"{field}: {err}", "danger")
    return redirect(url_for("tracepass.view_product", product_id=product.id))


# Code explanation: Implement the `update recall status` operation used by this part of TracePass.
@reporting_bp.route("/recalls/<int:recall_id>/status", methods=["POST"])
@login_required
@role_required(*CAN_MANAGE_EVIDENCE)
def update_recall_status(recall_id):
    from datetime import datetime, timezone
    recall = Recall.query.get_or_404(recall_id)
    form = RecallStatusForm()
    if form.validate_on_submit():
        recall.status = form.status.data
        if form.status.data == "closed":
            recall.closed_at = datetime.now(timezone.utc)
        db.session.commit()
        flash("Recall status updated.", "success")
    return redirect(url_for("tracepass.view_product", product_id=recall.product_id))


# --- incidents -----------------------------------------------------------------

# Code explanation: Implement the `report incident` operation used by this part of TracePass.
@reporting_bp.route("/products/<int:product_id>/incidents", methods=["POST"])
@login_required
def report_incident(product_id):
    # Any authenticated role can report an incident — customers included,
    # since they're often the ones who first notice a problem with a product.
    product = Product.query.get_or_404(product_id)
    form = IncidentForm()
    if form.validate_on_submit():
        incident = Incident(product_id=product.id, reported_by_user_id=current_user.id, description=form.description.data)
        db.session.add(incident)
        db.session.commit()
        flash("Incident reported.", "warning")
    else:
        for field, errors in form.errors.items():
            for err in errors:
                flash(f"{field}: {err}", "danger")
    return redirect(url_for("tracepass.view_product", product_id=product.id))


# Code explanation: Implement the `update incident status` operation used by this part of TracePass.
@reporting_bp.route("/incidents/<int:incident_id>/status", methods=["POST"])
@login_required
@role_required(*CAN_MANAGE_EVIDENCE)
def update_incident_status(incident_id):
    from datetime import datetime, timezone
    incident = Incident.query.get_or_404(incident_id)
    form = IncidentStatusForm()
    if form.validate_on_submit():
        incident.status = form.status.data
        incident.resolution_notes = form.resolution_notes.data
        if form.status.data == "resolved":
            incident.resolved_at = datetime.now(timezone.utc)
        db.session.commit()
        flash("Incident status updated.", "success")
    return redirect(url_for("tracepass.view_product", product_id=incident.product_id))


# --- audit log viewer (admin only) ----------------------------------------------

# Code explanation: Implement the `list audit logs` operation used by this part of TracePass.
@reporting_bp.route("/admin/audit-logs")
@login_required
@role_required(ROLE_ADMIN)
def list_audit_logs():
    query = AuditLog.query
    action = request.args.get("action", "").strip()
    entity_type = request.args.get("entity_type", "").strip()
    search = request.args.get("q", "").strip()
    if action in {"create", "update", "delete"}:
        query = query.filter_by(action=action)
    if entity_type:
        query = query.filter_by(entity_type=entity_type)
    if search:
        like = f"%{search}%"
        query = query.filter(db.or_(AuditLog.old_value.ilike(like), AuditLog.new_value.ilike(like)))
    page = request.args.get("page", 1, type=int)
    pagination = query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=25, error_out=False)
    entity_types = [row[0] for row in db.session.query(AuditLog.entity_type).distinct().order_by(AuditLog.entity_type).all()]
    return render_template("reporting/audit_logs.html", pagination=pagination, logs=pagination.items,
                           action=action, entity_type=entity_type, search=search, entity_types=entity_types)


# Code explanation: Implement the `export summary csv` operation used by this part of TracePass.
@reporting_bp.route("/reports/summary.csv")
@login_required
def export_summary_csv():
    scope_org_id = current_user.organization_id if current_user.has_role(ROLE_MANUFACTURER) else None
    kpis = compute_kpis(scope_org_id=scope_org_id)
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["TracePass Reporting Summary"])
    writer.writerow(["Generated", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")])
    writer.writerow([])
    writer.writerow(["Metric", "Value"])
    for key, value in kpis.items():
        writer.writerow([key.replace("_", " ").title(), value])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=tracepass_reporting_summary.csv"})


# --- PDF export ------------------------------------------------------------------

# Code explanation: Implement the `export compliance report` operation used by this part of TracePass.
@reporting_bp.route("/products/<int:product_id>/report.pdf")
@login_required
def export_compliance_report(product_id):
    product = Product.query.get_or_404(product_id)

    certificates = Certificate.query.filter(
        db.or_(Certificate.product_id == product.id, Certificate.organization_id == product.manufacturer_org_id)
    ).all()
    checks = ComplianceCheck.query.filter_by(product_id=product.id).order_by(ComplianceCheck.checked_at).all()
    reviews = ComplianceReview.query.filter_by(product_id=product.id).order_by(ComplianceReview.reviewed_at).all()

    reports_dir = os.path.join(current_app.instance_path, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    output_path = os.path.join(reports_dir, f"compliance_report_{product.passport_code}.pdf")

    build_compliance_report_pdf(product, certificates, checks, reviews, output_path)

    return send_file(output_path, as_attachment=True, download_name=f"TracePass_{product.passport_code}_compliance_report.pdf")
