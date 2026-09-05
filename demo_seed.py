
"""Create a presentation-ready TracePass end-to-end demo dataset.

Run after `flask db upgrade` and `python seed.py`:
    python demo_seed.py

The script is idempotent for its own TP-DEMO records: it reuses records when
possible and avoids changing ordinary user/project data. Demo passwords are
intended only for a local presentation environment.
"""
import json
import os
import shutil
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from flask import url_for

from app import create_app
from app.extensions import db
from app.models.role import Role, ROLE_ADMIN, ROLE_MANUFACTURER, ROLE_SUPPLIER, ROLE_DISTRIBUTOR, ROLE_RETAILER, ROLE_AUDITOR
from app.models.user import User
from app.models.organization import Organization
from app.models.supplier import Supplier
from app.models.supplier_material import SupplierMaterial
from app.models.material import Material
from app.models.product_category import ProductCategory
from app.models.product import Product, ProductBatch, ProductMaterial, QRCode, STATUS_PUBLISHED, COMPLIANCE_COMPLIANT
from app.models.supply_chain_event import SupplyChainEvent
from app.models.shipment import Shipment, SHIPMENT_DELIVERED
from app.models.purchase_order import PurchaseOrder, PO_RECEIVED
from app.models.certificate import Certificate, Document
from app.models.compliance import ComplianceRule, ComplianceRequirement, ComplianceCheck, ComplianceReview, REQ_TYPE_CERTIFICATE, REQ_TYPE_DOCUMENT, CHECK_PASS, REVIEW_APPROVED
from app.models.registration_request import RegistrationRequest, REQUEST_PENDING
from app.models.registration_request_document import RegistrationRequestDocument
from app.models.lifecycle import LifecycleEvent
from app.tracepass.utils import generate_qr_for_passport_code

app = create_app()
DEMO_PASSWORD = os.environ.get("DEMO_PASSWORD", "Demo1234!")
BASE_URL = os.environ.get("DEMO_BASE_URL", "http://127.0.0.1:5000")


#  Retrieves or create needed by the surrounding feature.
def get_or_create(model, filters, **values):
    obj = model.query.filter_by(**filters).first()
    if obj is None:
        obj = model(**filters, **values)
        db.session.add(obj)
        db.session.flush()
    return obj


# Implements the demo user operation used by this module.
def demo_user(email, name, role_name, organization=None):
    role = Role.query.filter_by(name=role_name).first()
    obj = User.query.filter_by(email=email).first()
    if obj is None:
        obj = User(name=name, email=email, role_id=role.id, organization_id=organization.id if organization else None, is_active=True)
        obj.set_password(DEMO_PASSWORD)
        db.session.add(obj)
        db.session.flush()
    else:
        obj.role_id = role.id
        obj.organization_id = organization.id if organization else None
        obj.is_active = True
    return obj


# Implements the organization operation used by this module.
def organization(name, org_type, reg_no, email, phone):
    return get_or_create(Organization, {"registration_no": reg_no}, name=name, type=org_type, contact_email=email, contact_phone=phone, address="Karachi, Sindh, Pakistan", is_verified=True)

with app.app_context():
    # Reuse the seeded Shirt category because it already has the required
    # Apparel template fields used by the passport readiness check.
    category = ProductCategory.query.filter_by(name="Shirt").first()
    if category is None:
        raise RuntimeError("Run python seed.py first so the Shirt category exists.")

    admin = User.query.filter_by(email=os.environ.get("SEED_ADMIN_EMAIL", "admin@tracepass.example")).first()
    if admin is None:
        admin = demo_user("admin@tracepass.demo", "TracePass Demo Admin", ROLE_ADMIN)

    manufacturer_org = organization("EcoWear Manufacturing (Demo)", "manufacturer", "TP-DEMO-MFG-001", "manufacturer@tracepass.demo", "+92-300-1000001")
    manufacturer2_org = organization("UrbanThread Manufacturing (Demo)", "manufacturer", "TP-DEMO-MFG-002", "manufacturer2@tracepass.demo", "+92-300-1000011")
    supplier_org = organization("GreenFiber Materials (Demo)", "supplier", "TP-DEMO-SUP-001", "supplier@tracepass.demo", "+92-300-1000002")
    supplier2_org = organization("ReTex Raw Materials (Demo)", "supplier", "TP-DEMO-SUP-002", "supplier2@tracepass.demo", "+92-300-1000012")
    distributor_org = organization("National Distribution Network (Demo)", "distributor", "TP-DEMO-DIS-001", "distributor@tracepass.demo", "+92-300-1000003")
    distributor2_org = organization("Metro Distribution Services (Demo)", "distributor", "TP-DEMO-DIS-002", "distributor2@tracepass.demo", "+92-300-1000013")
    retailer_org = organization("TracePass Retail Hub (Demo)", "retailer", "TP-DEMO-RET-001", "retailer@tracepass.demo", "+92-300-1000004")
    retailer2_org = organization("GreenStyle Retail (Demo)", "retailer", "TP-DEMO-RET-002", "retailer2@tracepass.demo", "+92-300-1000014")
    auditor_org = organization("Independent Compliance Audit Office (Demo)", "auditor", "TP-DEMO-AUD-001", "auditor@tracepass.demo", "+92-300-1000005")

    mfg_user = demo_user("manufacturer@tracepass.demo", "Ayesha Khan", ROLE_MANUFACTURER, manufacturer_org)
    mfg2_user = demo_user("manufacturer2@tracepass.demo", "Omar Farooq", ROLE_MANUFACTURER, manufacturer2_org)
    sup_user = demo_user("supplier@tracepass.demo", "Hassan Ali", ROLE_SUPPLIER, supplier_org)
    sup2_user = demo_user("supplier2@tracepass.demo", "Mariam Noor", ROLE_SUPPLIER, supplier2_org)
    dis_user = demo_user("distributor@tracepass.demo", "Bilal Ahmed", ROLE_DISTRIBUTOR, distributor_org)
    dis2_user = demo_user("distributor2@tracepass.demo", "Usman Raza", ROLE_DISTRIBUTOR, distributor2_org)
    ret_user = demo_user("retailer@tracepass.demo", "Sara Malik", ROLE_RETAILER, retailer_org)
    ret2_user = demo_user("retailer2@tracepass.demo", "Hina Tariq", ROLE_RETAILER, retailer2_org)
    aud_user = demo_user("auditor@tracepass.demo", "Nadia Shah", ROLE_AUDITOR, auditor_org)

    supplier_profile = Supplier.query.filter_by(organization_id=supplier_org.id).first()
    if supplier_profile is None:
        supplier_profile = Supplier(organization_id=supplier_org.id, material_categories_supplied="Cotton, Recycled Polyester", rating=4.8)
        db.session.add(supplier_profile)
        db.session.flush()

    cotton = get_or_create(Material, {"name": "Organic Cotton Fiber"}, category="Textile Fiber", origin_country="Pakistan", sustainability_notes="Organic fiber with controlled origin and reduced chemical input.")
    recycled = get_or_create(Material, {"name": "Recycled Polyester Fiber"}, category="Textile Fiber", origin_country="Pakistan", sustainability_notes="Post-consumer recycled polyester for durability and circularity.")
    if not SupplierMaterial.query.filter_by(supplier_id=supplier_profile.id, material_id=cotton.id).first():
        db.session.add(SupplierMaterial(supplier_id=supplier_profile.id, material_id=cotton.id, unit="KG", minimum_order_qty=100, lead_time_days=10, is_active=True))
    if not SupplierMaterial.query.filter_by(supplier_id=supplier_profile.id, material_id=recycled.id).first():
        db.session.add(SupplierMaterial(supplier_id=supplier_profile.id, material_id=recycled.id, unit="KG", minimum_order_qty=50, lead_time_days=7, is_active=True))

    supplier2_profile = Supplier.query.filter_by(organization_id=supplier2_org.id).first()
    if supplier2_profile is None:
        supplier2_profile = Supplier(organization_id=supplier2_org.id, material_categories_supplied="Recycled Fibers, Organic Cotton", rating=4.6)
        db.session.add(supplier2_profile); db.session.flush()
    for mat, minimum, lead in [(cotton, 80, 12), (recycled, 40, 8)]:
        if not SupplierMaterial.query.filter_by(supplier_id=supplier2_profile.id, material_id=mat.id).first():
            db.session.add(SupplierMaterial(supplier_id=supplier2_profile.id, material_id=mat.id, unit="KG", minimum_order_qty=minimum, lead_time_days=lead, is_active=True))

    # A rule that can be visibly demonstrated in the Compliance screen.
    rule = ComplianceRule.query.filter_by(name="TP-DEMO Apparel Certification Rule").first()
    if rule is None:
        rule = ComplianceRule(name="TP-DEMO Apparel Certification Rule", category_id=category.id, description="Demo rule: apparel passport requires approved ISO 14001 and OEKO-TEX evidence plus a test report.", is_active=True)
        db.session.add(rule); db.session.flush()
    reqs = [
        (REQ_TYPE_CERTIFICATE, "ISO 14001", "Environmental management certification", True),
        (REQ_TYPE_CERTIFICATE, "OEKO-TEX Standard 100", "Textile safety certification", True),
        (REQ_TYPE_DOCUMENT, "test_report", "Independent product test report", True),
    ]
    for typ, val, desc, mandatory in reqs:
        if not ComplianceRequirement.query.filter_by(rule_id=rule.id, requirement_type=typ, required_value=val).first():
            db.session.add(ComplianceRequirement(rule_id=rule.id, requirement_type=typ, required_value=val, description=desc, is_mandatory=mandatory))
    db.session.flush()

    product = Product.query.filter_by(passport_code="TP-DEMO-2026-001").first()
    if product is None:
        product = Product(
            passport_code="TP-DEMO-2026-001",
            name="EcoWear Organic Cotton T-Shirt",
            category=category.name,
            category_id=category.id,
            brand="EcoWear Demo",
            model="EW-TEE-001",
            description="Presentation-ready sustainable apparel product demonstrating the TracePass digital thread from raw materials to lifecycle and QR verification.",
            manufacturer_org_id=manufacturer_org.id,
            status=STATUS_PUBLISHED,
            compliance_status=COMPLIANCE_COMPLIANT,
            attribute_values=json.dumps({"material_composition": "90% Organic Cotton / 10% Recycled Polyester", "country_of_origin": "Pakistan", "recycled_content": 10}),
            sustainability_data=json.dumps({"recycled_content_percent": 10, "estimated_carbon_kg_co2e": 4.8, "water_saving_percent": 32, "repairability": "Designed for repair and extended use", "recyclability": "Mono-material dominant construction; textile recovery supported", "circularity_path": "Reuse → Repair → Recycling"}),
        )
        db.session.add(product); db.session.flush()
    else:
        product.status = STATUS_PUBLISHED
        product.compliance_status = COMPLIANCE_COMPLIANT

    # Use an existing bundled industry image as a presentation-safe product photo.
    source_img = Path(app.root_path) / "static" / "images" / "industries" / "apparel.jpg"
    product_dir = Path(app.config["UPLOAD_FOLDER"]) / "product_images"
    product_dir.mkdir(parents=True, exist_ok=True)
    demo_img = product_dir / "tp-demo-ecowear.jpg"
    if source_img.exists() and not demo_img.exists():
        shutil.copy2(source_img, demo_img)
    product.image_url = "/uploads/product_images/tp-demo-ecowear.jpg"

    batch = ProductBatch.query.filter_by(product_id=product.id, batch_no="TP-DEMO-BATCH-001").first()
    if batch is None:
        batch = ProductBatch(product_id=product.id, batch_no="TP-DEMO-BATCH-001", manufacture_date=date(2026, 8, 10), production_location="Karachi Garment Facility — Demo", quantity=1000)
        db.session.add(batch); db.session.flush()

    for mat, pct, qty in [(cotton, 90, 450.0), (recycled, 10, 50.0)]:
        link = ProductMaterial.query.filter_by(product_id=product.id, material_id=mat.id).first()
        if link is None:
            db.session.add(ProductMaterial(product_id=product.id, material_id=mat.id, supplier_id=supplier_profile.id, quantity=qty, percentage=pct))
        else:
            link.supplier_id = supplier_profile.id; link.quantity = qty; link.percentage = pct

    # Purchase order showing B2B sourcing.
    po = PurchaseOrder.query.filter_by(po_number="TP-DEMO-PO-001").first()
    if po is None:
        po = PurchaseOrder(po_number="TP-DEMO-PO-001", product_id=product.id, material_id=cotton.id, from_org_id=manufacturer_org.id, to_org_id=supplier_org.id, quantity=450, status=PO_RECEIVED, requested_delivery_date=date(2026,7,25), confirmed_quantity=450, confirmed_supply_date=date(2026,7,22), expected_delivery_date=date(2026,7,25), requested_by_user_id=mfg_user.id, responded_by_user_id=sup_user.id, responded_at=datetime(2026,7,18,tzinfo=timezone.utc), dispatched_at=datetime(2026,7,22,tzinfo=timezone.utc), delivered_at=datetime(2026,7,24,tzinfo=timezone.utc), received_at=datetime(2026,7,25,tzinfo=timezone.utc), notes="Demo raw-material procurement order.", agreed_unit_price=1850, agreed_total_price=832500, agreed_currency="PKR")
        db.session.add(po); db.session.flush()

    # Timeline events.
    events = [
        ("manufactured", datetime(2026,8,10,9,0,tzinfo=timezone.utc), manufacturer_org, "Karachi Garment Facility", "Batch manufactured and passport linked."),
        ("quality_check", datetime(2026,8,11,11,0,tzinfo=timezone.utc), auditor_org, "Karachi Quality Lab", "Quality inspection passed."),
        ("shipped", datetime(2026,8,12,10,0,tzinfo=timezone.utc), manufacturer_org, "Karachi Distribution Gate", "Finished goods dispatched."),
        ("delivered", datetime(2026,8,14,15,0,tzinfo=timezone.utc), distributor_org, "Lahore Distribution Center", "Shipment delivered to distributor."),
        ("received", datetime(2026,8,15,10,0,tzinfo=timezone.utc), distributor_org, "Lahore Distribution Center", "Distributor received and verified batch."),
        ("sold", datetime(2026,8,20,13,0,tzinfo=timezone.utc), retailer_org, "Retail Hub", "Product entered retail lifecycle."),
    ]
    for typ, dt, org, loc, notes in events:
        if not SupplyChainEvent.query.filter_by(product_id=product.id, event_type=typ, event_date=dt).first():
            db.session.add(SupplyChainEvent(product_id=product.id, batch_id=batch.id, organization_id=org.id, event_type=typ, location=loc, event_date=dt, notes=notes, recorded_by_user_id=(mfg_user.id if org.id == manufacturer_org.id else dis_user.id)))

    # Shipment through the distributor.
    if not Shipment.query.filter_by(tracking_no="TP-DEMO-TRK-001").first():
        db.session.add(Shipment(purchase_order_id=po.id, batch_id=batch.id, quantity=1000, from_org_id=manufacturer_org.id, to_org_id=distributor_org.id, tracking_no="TP-DEMO-TRK-001", status=SHIPMENT_DELIVERED, shipped_date=date(2026,8,12), expected_delivery_date=date(2026,8,14), received_date=date(2026,8,14)))

    # Lifecycle: enough events to demonstrate circularity and end-of-life planning.
    lifecycle = [
        ("reused", datetime(2026,8,25,10,0,tzinfo=timezone.utc), retailer_org, "Retail Hub", "Customer returned product for second-life reuse program."),
        ("repaired", datetime(2026,8,26,11,0,tzinfo=timezone.utc), manufacturer_org, "Repair Center", "Minor seam repair completed."),
        ("recycled", datetime(2026,8,28,14,0,tzinfo=timezone.utc), supplier_org, "Textile Recovery Center", "End-of-life textile recovery route recorded for demonstration."),
    ]
    for typ, dt, org, loc, notes in lifecycle:
        if not LifecycleEvent.query.filter_by(product_id=product.id, event_type=typ, event_date=dt).first():
            db.session.add(LifecycleEvent(product_id=product.id, event_type=typ, event_date=dt, organization_id=org.id, location=loc, notes=notes, recorded_by_user_id=ret_user.id if typ == "reused" else mfg_user.id))

    db.session.commit()

    # Generate sample evidence files using reportlab if available.
    evidence_dir = Path(app.config["UPLOAD_FOLDER"]) / "demo_evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    try:
        from reportlab.pdfgen import canvas
# Implements the make pdf operation used by this module.
        def make_pdf(filename, title, lines):
            path = evidence_dir / filename
            if not path.exists():
                c = canvas.Canvas(str(path)); c.setTitle(title); c.setFont("Helvetica-Bold", 16); c.drawString(50, 790, title)
                c.setFont("Helvetica", 10); y=755
                for line in lines:
                    c.drawString(50, y, line); y -= 18
                c.save()
            return path
        iso = make_pdf("TP-DEMO-ISO-14001.pdf", "ISO 14001 Environmental Management Certificate", ["Certificate No: TP-DEMO-ISO14001-001", "Organization: EcoWear Manufacturing (Demo)", "Status: Approved for TracePass demonstration", "Issue Date: 2026-01-15 | Expiry Date: 2027-01-15"])
        oeko = make_pdf("TP-DEMO-OEKO-TEX.pdf", "OEKO-TEX Standard 100 Certificate", ["Certificate No: TP-DEMO-OEKO-001", "Product: EcoWear Organic Cotton T-Shirt", "Status: Approved for TracePass demonstration", "Issue Date: 2026-02-01 | Expiry Date: 2027-02-01"])
        test = make_pdf("TP-DEMO-TEST-REPORT.pdf", "Independent Textile Test Report", ["Report No: TP-DEMO-TEST-001", "Product: EcoWear Organic Cotton T-Shirt", "Result: PASS — physical and colorfastness tests", "Laboratory: TracePass Demo Quality Laboratory"])
    except ImportError:
        iso = oeko = test = None

    #  Adds cert to the relevant application or database context.
    def add_cert(cert_type, number, path, issuing):
        cert = Certificate.query.filter_by(cert_number=number).first()
        if cert is None:
            cert = Certificate(product_id=product.id, organization_id=None, cert_type=cert_type, issuing_body=issuing, cert_number=number, issue_date=date(2026,1,1), expiry_date=date(2027,12,31), file_path=str(path.relative_to(Path(app.config["UPLOAD_FOLDER"]))).replace(os.sep, "/") if path else None, uploaded_by_user_id=mfg_user.id, review_status="approved", reviewed_by_user_id=aud_user.id, reviewed_at=datetime.now(timezone.utc), review_comments="Demo evidence reviewed and approved.")
            db.session.add(cert)
        return cert
    if iso and oeko:
        add_cert("ISO 14001", "TP-DEMO-ISO14001-001", iso, "Demo Certification Body")
        add_cert("OEKO-TEX Standard 100", "TP-DEMO-OEKO-001", oeko, "Demo Textile Certification Body")
        db.session.flush()
        if not Document.query.filter_by(product_id=product.id, doc_type="test_report").first():
            db.session.add(Document(product_id=product.id, doc_type="test_report", file_path=str(test.relative_to(Path(app.config["UPLOAD_FOLDER"]))).replace(os.sep, "/"), uploaded_by_user_id=mfg_user.id))
    db.session.commit()

    # Rebuild compliance evidence history for this demo product if necessary.
    if ComplianceCheck.query.filter_by(product_id=product.id).count() == 0:
        from app.compliance.engine import evaluate_product_compliance
        evaluate_product_compliance(product)
    else:
        product.compliance_status = COMPLIANCE_COMPLIANT
        db.session.commit()
    if not ComplianceReview.query.filter_by(product_id=product.id).first():
        db.session.add(ComplianceReview(product_id=product.id, reviewer_user_id=aud_user.id, decision=REVIEW_APPROVED, reasoning="Demo audit review: required evidence present and traceability chain complete.", reviewed_at=datetime.now(timezone.utc)))
        product.compliance_status = COMPLIANCE_COMPLIANT
        db.session.commit()

    # Create a QR code that points to the public passport on the local demo host.
    with app.test_request_context(base_url=BASE_URL):
        if product.qr_code is None:
            code_value = generate_qr_for_passport_code(product.passport_code)
            db.session.add(QRCode(product_id=product.id, code_value=code_value))
            db.session.commit()
        verify_url = url_for("tracepass.verify_passport", passport_code=product.passport_code, _external=True)

    # Create one pending registration request with authenticity evidence so the
    # committee can demonstrate the controlled onboarding workflow as well.
    demo_request = RegistrationRequest.query.filter_by(email="applicant@demo-industries.test", status=REQUEST_PENDING).first()
    if demo_request is None:
        demo_request = RegistrationRequest(
            name="Hamza Siddiqui", email="applicant@demo-industries.test", phone="+92-300-5550000",
            requested_role="manufacturer", organization_name="Demo Industries (Pending Verification)",
            registration_no="TP-DEMO-REQ-001", organization_type="manufacturer",
            organization_email="verification@demo-industries.test", organization_phone="+92-300-5550001",
            address="Karachi, Sindh, Pakistan", reason="Demonstration account request for committee onboarding workflow.", status=REQUEST_PENDING,
        )
        demo_request.set_password(DEMO_PASSWORD)
        db.session.add(demo_request); db.session.flush()
        try:
            from reportlab.pdfgen import canvas
            req_dir = Path(app.config["UPLOAD_FOLDER"]) / "registration_requests" / str(demo_request.id)
            req_dir.mkdir(parents=True, exist_ok=True)
            for filename, title, body in [
                ("company_registration.pdf", "Company Registration Certificate", "Demo Industries | Registration No. TP-DEMO-REQ-001"),
                ("tax_registration.pdf", "Tax Registration Evidence", "Demo Industries | Tax/Business registration evidence for demonstration"),
            ]:
                path = req_dir / filename
                c = canvas.Canvas(str(path)); c.setFont("Helvetica-Bold", 16); c.drawString(50, 790, title); c.setFont("Helvetica", 11); c.drawString(50, 755, body); c.drawString(50, 730, "STATUS: DEMONSTRATION DOCUMENT"); c.save()
                db.session.add(RegistrationRequestDocument(registration_request_id=demo_request.id, document_type="authenticity_evidence", original_filename=filename, file_path=str(path.relative_to(Path(app.config["UPLOAD_FOLDER"]))).replace(os.sep, "/")))
        except ImportError:
            pass
        db.session.commit()

    print("\nTracePass demo dataset is ready.")
    print("Demo users (password for all):", DEMO_PASSWORD)
    for email in ["manufacturer@tracepass.demo", "manufacturer2@tracepass.demo", "supplier@tracepass.demo", "supplier2@tracepass.demo", "distributor@tracepass.demo", "distributor2@tracepass.demo", "retailer@tracepass.demo", "retailer2@tracepass.demo", "auditor@tracepass.demo"]:
        print(" -", email)
    print("Product passport:", product.passport_code)
    print("Public verification URL:", verify_url)
    print("QR code value:", product.qr_code.code_value if product.qr_code else "not generated")
