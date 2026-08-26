# TracePass code note: This module implements the tests/test_core_requirements.py part of the application.
"""
Covers the Testing Expectations (spec section 27) that test_api.py didn't
touch: auth/role permissions, business-rule calculations, validation of
invalid input, an end-to-end workflow, and file-upload/download restrictions.
"""
import io

import pytest

from app.extensions import db
from app.models.role import Role, ROLE_ADMIN, ROLE_MANUFACTURER, ROLE_AUDITOR, ROLE_CUSTOMER
from app.models.user import User
from app.models.organization import Organization
from app.models.product import Product, COMPLIANCE_COMPLIANT, COMPLIANCE_NON_COMPLIANT, COMPLIANCE_PENDING
from app.models.certificate import Certificate, Document
from app.models.compliance import ComplianceRule, ComplianceRequirement
from app.models.product_category import ProductCategory
from app.compliance.engine import evaluate_product_compliance


# Code explanation: Authenticate the submitted credentials and create the Flask-Login session.
def login(client, email, password):
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=True)


# Code explanation: Implement the `make user` operation used by this part of TracePass.
def make_user(role_name, email, org=None, password="TestPass123!"):
    role = Role.query.filter_by(name=role_name).first()
    user = User(name=f"Test {role_name}", email=email, role_id=role.id,
                organization_id=org.id if org else None)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


# --- authentication & role permissions --------------------------------------

# Code explanation: Implement the `test protected page redirects anonymous user to login` operation used by this part of TracePass.
def test_protected_page_redirects_anonymous_user_to_login(client):
    response = client.get("/dashboard")
    assert response.status_code in (302, 401)


# Code explanation: Implement the `test customer cannot reach admin only route` operation used by this part of TracePass.
def test_customer_cannot_reach_admin_only_route(client, app):
    with app.app_context():
        make_user(ROLE_CUSTOMER, "customer@example.com")
    login(client, "customer@example.com", "TestPass123!")
    response = client.get("/admin/compliance-rules")
    assert response.status_code == 403


# Code explanation: Implement the `test admin can reach admin only route` operation used by this part of TracePass.
def test_admin_can_reach_admin_only_route(client, app):
    with app.app_context():
        make_user(ROLE_ADMIN, "admin2@example.com")
    login(client, "admin2@example.com", "TestPass123!")
    response = client.get("/admin/compliance-rules")
    assert response.status_code == 200


# Code explanation: Implement the `test deactivated user cannot log in` operation used by this part of TracePass.
def test_deactivated_user_cannot_log_in(client, app):
    with app.app_context():
        user = make_user(ROLE_CUSTOMER, "inactive@example.com")
        user.is_active = False
        db.session.commit()
    response = login(client, "inactive@example.com", "TestPass123!")
    assert b"deactivated" in response.data.lower()


# --- registration / validation of invalid input ------------------------------

# Code explanation: Implement the `test registration rejects duplicate email` operation used by this part of TracePass.
def test_registration_rejects_duplicate_email(client, app):
    with app.app_context():
        make_user(ROLE_CUSTOMER, "dup@example.com")
    response = client.post(
        "/register",
        data={
            "name": "Second Person",
            "email": "dup@example.com",
            "password": "AnotherPass1!",
            "confirm_password": "AnotherPass1!",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"already exists" in response.data


# Code explanation: Implement the `test registration rejects mismatched passwords` operation used by this part of TracePass.
def test_registration_rejects_mismatched_passwords(client, app):
    response = client.post(
        "/register",
        data={
            "name": "Someone",
            "email": "mismatch@example.com",
            "password": "AnotherPass1!",
            "confirm_password": "DifferentPass1!",
        },
        follow_redirects=True,
    )
    with app.app_context():
        assert User.query.filter_by(email="mismatch@example.com").first() is None


# Code explanation: Implement the `test login rejects wrong password` operation used by this part of TracePass.
def test_login_rejects_wrong_password(client, app):
    with app.app_context():
        make_user(ROLE_CUSTOMER, "wrongpass@example.com")
    response = login(client, "wrongpass@example.com", "NotTheRealPassword")
    assert b"Invalid email or password" in response.data


# --- compliance engine business rules ----------------------------------------

# Code explanation: Implement the `test compliance pending when no rules apply` operation used by this part of TracePass.
def test_compliance_pending_when_no_rules_apply(app):
    with app.app_context():
        org = Organization(name="Acme Manufacturing", type="manufacturer")
        db.session.add(org)
        db.session.flush()
        product = Product(name="Widget", manufacturer_org_id=org.id, category="widgets")
        db.session.add(product)
        db.session.commit()

        summary = evaluate_product_compliance(product)
        assert summary["resulting_status"] == COMPLIANCE_PENDING
        assert product.compliance_status == COMPLIANCE_PENDING


# Code explanation: Implement the `test compliance non compliant when mandatory certificate missing` operation used by this part of TracePass.
def test_compliance_non_compliant_when_mandatory_certificate_missing(app):
    with app.app_context():
        org = Organization(name="Acme Manufacturing 2", type="manufacturer")
        db.session.add(org)
        db.session.flush()
        category = ProductCategory(name="widgets")
        db.session.add(category)
        db.session.flush()
        product = Product(name="Widget 2", manufacturer_org_id=org.id, category="widgets", category_id=category.id)
        db.session.add(product)

        rule = ComplianceRule(name="Widget Safety", category_id=category.id, is_active=True)
        db.session.add(rule)
        db.session.flush()
        requirement = ComplianceRequirement(
            rule_id=rule.id, requirement_type="certificate",
            required_value="CE Mark", is_mandatory=True,
        )
        db.session.add(requirement)
        db.session.commit()

        summary = evaluate_product_compliance(product)
        assert summary["mandatory_failed"] == 1
        assert product.compliance_status == COMPLIANCE_NON_COMPLIANT


# Code explanation: Implement the `test compliance compliant when valid certificate present` operation used by this part of TracePass.
def test_compliance_compliant_when_valid_certificate_present(app):
    with app.app_context():
        org = Organization(name="Acme Manufacturing 3", type="manufacturer")
        db.session.add(org)
        db.session.flush()
        category = ProductCategory(name="widgets3")
        db.session.add(category)
        db.session.flush()
        product = Product(name="Widget 3", manufacturer_org_id=org.id, category="widgets3", category_id=category.id)
        db.session.add(product)

        rule = ComplianceRule(name="Widget Safety 2", category_id=category.id, is_active=True)
        db.session.add(rule)
        db.session.flush()
        requirement = ComplianceRequirement(
            rule_id=rule.id, requirement_type="certificate",
            required_value="CE Mark", is_mandatory=True,
        )
        db.session.add(requirement)
        db.session.flush()

        cert = Certificate(product_id=product.id, cert_type="CE Mark", expiry_date=None, review_status="approved")
        db.session.add(cert)
        db.session.commit()

        summary = evaluate_product_compliance(product)
        assert summary["mandatory_failed"] == 0
        assert product.compliance_status == COMPLIANCE_COMPLIANT


# Code explanation: Implement the `test compliance fails on expired certificate` operation used by this part of TracePass.
def test_compliance_fails_on_expired_certificate(app):
    from datetime import date, timedelta

    with app.app_context():
        org = Organization(name="Acme Manufacturing 4", type="manufacturer")
        db.session.add(org)
        db.session.flush()
        category = ProductCategory(name="widgets4")
        db.session.add(category)
        db.session.flush()
        product = Product(name="Widget 4", manufacturer_org_id=org.id, category="widgets4", category_id=category.id)
        db.session.add(product)

        rule = ComplianceRule(name="Widget Safety 3", category_id=category.id, is_active=True)
        db.session.add(rule)
        db.session.flush()
        requirement = ComplianceRequirement(
            rule_id=rule.id, requirement_type="certificate",
            required_value="CE Mark", is_mandatory=True,
        )
        db.session.add(requirement)
        db.session.flush()

        expired_cert = Certificate(
            product_id=product.id, cert_type="CE Mark",
            expiry_date=date.today() - timedelta(days=1),
            review_status="approved",
        )
        db.session.add(expired_cert)
        db.session.commit()

        summary = evaluate_product_compliance(product)
        assert summary["mandatory_failed"] == 1
        assert product.compliance_status == COMPLIANCE_NON_COMPLIANT


# --- file upload / download restrictions -------------------------------------

# Code explanation: Implement the `test document upload rejects disallowed extension` operation used by this part of TracePass.
def test_document_upload_rejects_disallowed_extension(client, app):
    with app.app_context():
        org = Organization(name="Acme Manufacturing 5", type="manufacturer")
        db.session.add(org)
        db.session.flush()
        product = Product(name="Widget 5", manufacturer_org_id=org.id)
        db.session.add(product)
        make_user(ROLE_MANUFACTURER, "manufacturer@example.com", org=org)
        db.session.commit()
        product_id = product.id

    login(client, "manufacturer@example.com", "TestPass123!")
    data = {
        "doc_type": "test_report",
        "file": (io.BytesIO(b"not a real executable, just bytes"), "malware.exe"),
    }
    response = client.post(
        f"/products/{product_id}/documents",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert Document.query.filter_by(product_id=product_id).count() == 0


# Code explanation: Implement the `test certificate download requires permitted role` operation used by this part of TracePass.
def test_certificate_download_requires_permitted_role(client, app):
    with app.app_context():
        org = Organization(name="Acme Manufacturing 6", type="manufacturer")
        db.session.add(org)
        db.session.flush()
        product = Product(name="Widget 6", manufacturer_org_id=org.id)
        db.session.add(product)
        db.session.flush()
        cert = Certificate(product_id=product.id, cert_type="ISO 9001", file_path="doesnotmatter.pdf")
        db.session.add(cert)
        make_user(ROLE_CUSTOMER, "customer2@example.com")
        db.session.commit()
        cert_id = cert.id

    login(client, "customer2@example.com", "TestPass123!")
    response = client.get(f"/certificates/{cert_id}/file")
    assert response.status_code == 403


# Code explanation: Implement the `test certificate download allows auditor` operation used by this part of TracePass.
def test_certificate_download_allows_auditor(client, app):
    with app.app_context():
        org = Organization(name="Acme Manufacturing 7", type="manufacturer")
        db.session.add(org)
        db.session.flush()
        product = Product(name="Widget 7", manufacturer_org_id=org.id)
        db.session.add(product)
        db.session.flush()
        cert = Certificate(product_id=product.id, cert_type="ISO 9001", file_path=None)
        db.session.add(cert)
        make_user(ROLE_AUDITOR, "auditor@example.com")
        db.session.commit()
        cert_id = cert.id

    login(client, "auditor@example.com", "TestPass123!")
    # No file was ever attached, so this should 404, not 403 — proving the
    # auditor cleared the role check and only failed on "no such file".
    response = client.get(f"/certificates/{cert_id}/file")
    assert response.status_code == 404


# --- end-to-end core business workflow ---------------------------------------
# Registration -> passport creation -> material/batch linking -> compliance ->
# publication -> public QR verification (spec sections 3, 7, 12).

# Code explanation: Implement the `test full passport lifecycle from creation to public verification` operation used by this part of TracePass.
def test_full_passport_lifecycle_from_creation_to_public_verification(client, app):
    from app.models.material import Material

    with app.app_context():
        org = Organization(name="Fabrikam Apparel", type="manufacturer", is_verified=True)
        db.session.add(org)
        material = Material(name="Organic Cotton", category="textile")
        db.session.add(material)
        db.session.flush()
        product = Product(
            name="Classic Tee",
            category="apparel",
            manufacturer_org_id=org.id,
        )
        db.session.add(product)
        make_user(ROLE_MANUFACTURER, "workflow-mfg@example.com", org=org)
        db.session.commit()
        product_id = product.id
        material_id = material.id

    login(client, "workflow-mfg@example.com", "TestPass123!")

    # 1. Publishing too early must be refused — no batch, no material yet.
    resp = client.post(f"/products/{product_id}/publish", follow_redirects=True)
    assert b"Cannot publish" in resp.data
    with app.app_context():
        assert db.session.get(Product, product_id).status != "published"

    # 2. Add the missing batch and a fully-accounted material composition.
    client.post(
        f"/products/{product_id}/batches",
        data={"batch_no": "B-001", "quantity": "500"},
        follow_redirects=True,
    )
    client.post(
        f"/products/{product_id}/materials",
        data={"material_id": str(material_id), "supplier_id": "0", "percentage": "100"},
        follow_redirects=True,
    )

    # 3. Now publication should succeed and mint a QR code.
    resp = client.post(f"/products/{product_id}/publish", follow_redirects=True)
    assert b"published" in resp.data.lower()
    with app.app_context():
        product = db.session.get(Product, product_id)
        assert product.status == "published"
        assert product.qr_code is not None
        code = product.passport_code

    # 4. The public, unauthenticated verification surfaces now work.
    public_resp = client.get(f"/verify/{code}")
    assert public_resp.status_code == 200

    api_resp = client.get(f"/api/v1/public/passports/{code}")
    assert api_resp.status_code == 200
    assert api_resp.get_json()["passport_code"] == code
