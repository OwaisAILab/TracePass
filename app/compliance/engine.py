from app.extensions import db
from app.models.compliance import ComplianceRule, ComplianceRequirement, ComplianceCheck, CHECK_PASS, CHECK_FAIL
from app.models.certificate import Certificate, Document
from app.models.product import Product, COMPLIANCE_COMPLIANT, COMPLIANCE_NON_COMPLIANT, COMPLIANCE_PENDING


def applicable_rules_for(product: Product):
    return ComplianceRule.query.filter(
        ComplianceRule.is_active.is_(True),
        db.or_(ComplianceRule.category_id.is_(None), ComplianceRule.category_id == product.category_id),
    ).all()


def _requirement_satisfied(product: Product, requirement: ComplianceRequirement):
    if requirement.requirement_type == "certificate":
        cert = (
            Certificate.query.filter(
                Certificate.cert_type == requirement.required_value,
                db.or_(
                    Certificate.product_id == product.id,
                    Certificate.organization_id == product.manufacturer_org_id,
                ),
                Certificate.review_status == "approved",
            )
            .order_by(Certificate.expiry_date.desc().nullslast())
            .first()
        )
        if cert is None:
            return False, f"No approved '{requirement.required_value}' certificate found."
        if cert.is_expired():
            return False, f"'{requirement.required_value}' certificate expired on {cert.expiry_date}."
        return True, f"Approved '{requirement.required_value}' certificate on file (expires {cert.expiry_date or 'never'})."

    if requirement.requirement_type == "document":
        doc = Document.query.filter_by(product_id=product.id, doc_type=requirement.required_value).first()
        if doc is None:
            return False, f"No '{requirement.required_value}' document found."
        return True, f"'{requirement.required_value}' document on file."

    return False, f"Unknown requirement type '{requirement.requirement_type}'."


def evaluate_product_compliance(product: Product) -> dict:
    rules = applicable_rules_for(product)
    new_checks = []
    mandatory_failed = passed = failed = 0

    for rule in rules:
        for requirement in rule.requirements:
            ok, reason = _requirement_satisfied(product, requirement)
            check = ComplianceCheck(
                product_id=product.id, rule_id=rule.id, requirement_id=requirement.id,
                result=CHECK_PASS if ok else CHECK_FAIL, reason=reason,
            )
            db.session.add(check)
            new_checks.append(check)
            if ok:
                passed += 1
            else:
                failed += 1
                if requirement.is_mandatory:
                    mandatory_failed += 1

    if not rules:
        product.compliance_status = COMPLIANCE_PENDING
    elif mandatory_failed > 0:
        product.compliance_status = COMPLIANCE_NON_COMPLIANT
    else:
        product.compliance_status = COMPLIANCE_COMPLIANT

    db.session.commit()
    return {
        "rules_checked": len(rules), "requirements_checked": len(new_checks),
        "passed": passed, "failed": failed, "mandatory_failed": mandatory_failed,
        "new_checks": new_checks, "resulting_status": product.compliance_status,
    }
