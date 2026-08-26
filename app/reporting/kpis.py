# TracePass code note: This module implements the app/reporting/kpis.py part of the application.
from app.models.product import Product, COMPLIANCE_COMPLIANT, COMPLIANCE_NON_COMPLIANT, COMPLIANCE_PENDING, STATUS_PUBLISHED
from app.models.certificate import Certificate
from app.models.compliance import ComplianceReview
from app.models.recall_incident import Recall, Incident, RECALL_OPEN, INCIDENT_OPEN


# Code explanation: Implement the `compute kpis` operation used by this part of TracePass.
def compute_kpis(scope_org_id=None):
    """
    Computes headline KPIs. If scope_org_id is given, scopes to that
    manufacturer's products only (used for manufacturer dashboards);
    otherwise covers everything (admin/auditor view).
    """
    query = Product.query
    if scope_org_id is not None:
        query = query.filter_by(manufacturer_org_id=scope_org_id)

    total = query.count()
    compliant = query.filter_by(compliance_status=COMPLIANCE_COMPLIANT).count()
    non_compliant = query.filter_by(compliance_status=COMPLIANCE_NON_COMPLIANT).count()
    pending = query.filter_by(compliance_status=COMPLIANCE_PENDING).count()
    published = query.filter_by(status=STATUS_PUBLISHED).count()

    pct_compliant = round((compliant / total) * 100, 1) if total else 0.0

    cert_query = Certificate.query
    expired_certs = sum(1 for c in cert_query.all() if c.is_expired())
    expiring_certs = sum(1 for c in cert_query.all() if c.expires_soon(30) and not c.is_expired())

    review_query = ComplianceReview.query
    approved_reviews = review_query.filter_by(decision="approved").count()

    recall_query = Recall.query.filter_by(status=RECALL_OPEN)
    incident_query = Incident.query.filter_by(status=INCIDENT_OPEN)
    if scope_org_id is not None:
        recall_query = recall_query.join(Product).filter(Product.manufacturer_org_id == scope_org_id)
        incident_query = incident_query.join(Product).filter(Product.manufacturer_org_id == scope_org_id)

    return {
        "total_products": total,
        "published_products": published,
        "compliant": compliant,
        "non_compliant": non_compliant,
        "pending": pending,
        "pct_compliant": pct_compliant,
        "expired_certs": expired_certs,
        "expiring_certs": expiring_certs,
        "approved_reviews": approved_reviews,
        "open_recalls": recall_query.count(),
        "open_incidents": incident_query.count(),
    }
