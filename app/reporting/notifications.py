
"""
Notification generation. Rather than a background scheduler (out of scope
for this phase), notifications are generated on-demand by calling
generate_notifications_for_user() — cheapest place to call this is right
before rendering the dashboard, so notifications are always fresh when
someone actually looks at them.

Each notification is deduplicated by (user_id, notif_type, product_id) so
re-running this doesn't spam the same alert every time the dashboard loads.
"""

from datetime import date, timedelta
from app.extensions import db
from app.models.certificate import Certificate
from app.models.compliance import ComplianceCheck, ComplianceReview, CHECK_FAIL
from app.models.product import Product
from app.models.recall_incident import Recall, RECALL_OPEN
from app.models.notification import (
    Notification,
    NOTIF_CERT_EXPIRING,
    NOTIF_CHECK_FAILED,
    NOTIF_REVIEW_PENDING,
    NOTIF_RECALL_ISSUED,
)
from app.models.role import ROLE_ADMIN, ROLE_MANUFACTURER, ROLE_AUDITOR


# Provides the internal create if new helper used by this module.
def _create_if_new(user_id, notif_type, message, product_id=None):
    exists = Notification.query.filter_by(user_id=user_id, notif_type=notif_type, product_id=product_id).first()
    if exists is None:
        db.session.add(Notification(user_id=user_id, notif_type=notif_type, message=message, product_id=product_id))
        return True
    return False


#  Generates notifications for user from the available project data.
def generate_notifications_for_user(user):
    """Generates any notifications this user doesn't already have, scoped to their role."""
    created = 0

    if user.has_role(ROLE_ADMIN, ROLE_MANUFACTURER):
        # Certificates expiring within 30 days, scoped to this manufacturer's org (or all, if admin)
        certs = Certificate.query.filter(Certificate.expiry_date.isnot(None)).all()
        for cert in certs:
            if not cert.expires_soon(30) and not cert.is_expired():
                continue
            if user.has_role(ROLE_MANUFACTURER) and cert.organization_id != user.organization_id:
                if not (cert.product and cert.product.manufacturer_org_id == user.organization_id):
                    continue
            status = "expired" if cert.is_expired() else "expiring soon"
            msg = f"Certificate '{cert.cert_type}' is {status} (expiry {cert.expiry_date})."
            if _create_if_new(user.id, NOTIF_CERT_EXPIRING, msg, product_id=cert.product_id):
                created += 1

    if user.has_role(ROLE_ADMIN, ROLE_MANUFACTURER, ROLE_AUDITOR):
        # Recently failed mandatory compliance checks
        failed_checks = (
            ComplianceCheck.query.filter_by(result=CHECK_FAIL)
            .join(Product)
            .all()
        )
        for check in failed_checks:
            if user.has_role(ROLE_MANUFACTURER) and check.product.manufacturer_org_id != user.organization_id:
                continue
            msg = f"Compliance check failed for '{check.product.name}': {check.reason}"
            if _create_if_new(user.id, NOTIF_CHECK_FAILED, msg, product_id=check.product_id):
                created += 1

    if user.has_role(ROLE_ADMIN, ROLE_AUDITOR):
        # Products that are non-compliant but have no review yet -> pending review
        pending = Product.query.filter_by(compliance_status="non_compliant").all()
        for product in pending:
            has_review = ComplianceReview.query.filter_by(product_id=product.id).first() is not None
            if has_review:
                continue
            msg = f"'{product.name}' is non-compliant and awaiting officer review."
            if _create_if_new(user.id, NOTIF_REVIEW_PENDING, msg, product_id=product.id):
                created += 1

    if user.has_role(ROLE_ADMIN, ROLE_MANUFACTURER):
        recalls = Recall.query.filter_by(status=RECALL_OPEN).all()
        for recall in recalls:
            if user.has_role(ROLE_MANUFACTURER) and recall.product.manufacturer_org_id != user.organization_id:
                continue
            msg = f"Active recall on '{recall.product.name}': {recall.reason}"
            if _create_if_new(user.id, NOTIF_RECALL_ISSUED, msg, product_id=recall.product_id):
                created += 1

    if created:
        db.session.commit()
    return created
