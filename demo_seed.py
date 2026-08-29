"""Populate a presentation-ready TracePass demonstration dataset.
Safe to run repeatedly: records are created only when the demo records do not exist.
Demo password for non-admin users: Demo1234!
"""
from datetime import datetime, date, timezone
import json
from app import create_app
from app.extensions import db
from app.models.role import Role, ROLE_ADMIN, ROLE_MANUFACTURER, ROLE_SUPPLIER, ROLE_DISTRIBUTOR, ROLE_RETAILER, ROLE_AUDITOR
from app.models.user import User
from app.models.organization import Organization
from app.models.material import Material
from app.models.supplier import Supplier
from app.models.product import Product, ProductBatch, ProductMaterial, QRCode, STATUS_PUBLISHED, COMPLIANCE_COMPLIANT
from app.models.product_category import ProductCategory
from app.models.supply_chain_event import SupplyChainEvent
from app.models.shipment import Shipment, SHIPMENT_DELIVERED
from app.models.lifecycle import LifecycleEvent
from app.models.verification import VerificationLog
from app.tracepass.utils import generate_qr_for_passport_code

app = create_app()

with app.app_context():
    roles = {r.name: r for r in Role.query.all()}
    def org(name, typ, reg):
        x = Organization.query.filter_by(registration_no=reg).first()
        if not x:
            x = Organization(name=name, type=typ, registration_no=reg, contact_email=f"info@{typ}.tracepass.demo", is_verified=True)
            db.session.add(x); db.session.flush()
        return x
    manufacturer = org("GreenThread Manufacturing Ltd.", "manufacturer", "DEMO-MFG-001")
    supplier_org = org("EcoFiber Materials Co.", "supplier", "DEMO-SUP-001")
    distributor = org("TraceLogix Distribution", "distributor", "DEMO-DIS-001")
    retailer = org("CircularWear Retail", "retailer", "DEMO-RET-001")
    auditor_org = org("Independent DPP Audit Bureau", "auditor", "DEMO-AUD-001")

    def user(email, name, role, organization=None):
        x = User.query.filter_by(email=email).first()
        if not x:
            x = User(name=name, email=email, role_id=roles[role].id, organization_id=organization.id if organization else None)
            x.set_password("Demo1234!"); db.session.add(x); db.session.flush()
        return x
    admin = user("admin@tracepass.demo", "TracePass Administrator", ROLE_ADMIN)
    manufacturer_user = user("manufacturer@tracepass.demo", "Ayesha Khan", ROLE_MANUFACTURER, manufacturer)
    supplier_user = user("supplier@tracepass.demo", "Bilal Ahmed", ROLE_SUPPLIER, supplier_org)
    distributor_user = user("distributor@tracepass.demo", "Sara Ali", ROLE_DISTRIBUTOR, distributor)
    auditor_user = user("auditor@tracepass.demo", "Omar Hassan", ROLE_AUDITOR, auditor_org)
    retailer_user = user("retailer@tracepass.demo", "Mariam Shah", ROLE_RETAILER, retailer)

    material = Material.query.filter_by(name="Recycled Organic Cotton").first()
    if not material:
        material = Material(name="Recycled Organic Cotton", category="Textile", origin_country="Pakistan", sustainability_notes="GRS-style recycled content demonstration material.")
        db.session.add(material); db.session.flush()
    supplier = Supplier.query.filter_by(organization_id=supplier_org.id).first()
    if not supplier:
        supplier = Supplier(organization_id=supplier_org.id, material_categories_supplied="Textiles, Cotton", rating=4.8)
        db.session.add(supplier); db.session.flush()

    category = ProductCategory.query.filter_by(name="Shirt").first()
    product = Product.query.filter_by(passport_code="TP-DEMO2026").first()
    if not product:
        product = Product(passport_code="TP-DEMO2026", name="EcoTech Recycled Cotton Shirt", category_id=category.id, category=category.name,
                          brand="TraceWear", model="TW-RC-2026", description="Presentation-ready example of a general-purpose Digital Product Passport.",
                          manufacturer_org_id=manufacturer.id, status=STATUS_PUBLISHED, compliance_status=COMPLIANCE_COMPLIANT,
                          attribute_values=json.dumps({"material_composition":"100% recycled organic cotton","country_of_origin":"Pakistan","recycled_content":"85"}),
                          sustainability_data="Recycled content: 85%\nRepairability: Designed for repair and component replacement\nRecyclability: Textile recycling pathway available\nCircularity: Reuse → Refurbishment → Recycling")
        db.session.add(product); db.session.flush()
    else:
        product.status = STATUS_PUBLISHED; product.compliance_status = COMPLIANCE_COMPLIANT

    batch = ProductBatch.query.filter_by(product_id=product.id, batch_no="BATCH-2026-001").first()
    if not batch:
        batch = ProductBatch(product_id=product.id, batch_no="BATCH-2026-001", manufacture_date=date(2026,8,15), production_location="Karachi, Pakistan", quantity=500)
        db.session.add(batch); db.session.flush()
    if not ProductMaterial.query.filter_by(product_id=product.id, material_id=material.id).first():
        db.session.add(ProductMaterial(product_id=product.id, material_id=material.id, supplier_id=supplier.id, quantity=500, percentage=100))

    def event(etype, when, organization, location, notes):
        if not SupplyChainEvent.query.filter_by(product_id=product.id, event_type=etype, event_date=when).first():
            db.session.add(SupplyChainEvent(product_id=product.id, batch_id=batch.id, organization_id=organization.id, event_type=etype, event_date=when, location=location, notes=notes, recorded_by_user_id=manufacturer_user.id))
    event("manufactured", datetime(2026,8,15,9,0), manufacturer, "Karachi", "Batch manufactured and passport data initialized.")
    event("quality_check", datetime(2026,8,16,11,0), manufacturer, "Karachi QC Lab", "Quality inspection passed.")
    event("shipped", datetime(2026,8,18,8,30), distributor, "Karachi Port", "Outbound shipment released to distribution partner.")
    event("delivered", datetime(2026,8,20,15,0), distributor, "Lahore Distribution Hub", "Shipment received at distribution hub.")

    lifecycle = [
        ("reused", datetime(2026,8,21,10,0), retailer, "Lahore", "Demonstration circularity event: product eligible for reuse."),
        ("repaired", datetime(2026,8,22,14,0), retailer, "Lahore Repair Center", "Minor seam repair completed; product returned to service."),
    ]
    for et, when, o, loc, notes in lifecycle:
        if not LifecycleEvent.query.filter_by(product_id=product.id, event_type=et, event_date=when).first():
            db.session.add(LifecycleEvent(product_id=product.id, event_type=et, event_date=when, organization_id=o.id, location=loc, notes=notes, recorded_by_user_id=manufacturer_user.id))

    if not Shipment.query.filter_by(batch_id=batch.id, tracking_no="TP-DEMO-TRACK-001").first():
        db.session.add(Shipment(batch_id=batch.id, quantity=250, from_org_id=manufacturer.id, to_org_id=distributor.id, tracking_no="TP-DEMO-TRACK-001", status=SHIPMENT_DELIVERED, shipped_date=date(2026,8,18), expected_delivery_date=date(2026,8,20), received_date=date(2026,8,20)))

    if not product.qr_code:
        code = generate_qr_for_passport_code(product.passport_code)
        db.session.add(QRCode(product_id=product.id, code_value=code))
    if not VerificationLog.query.filter_by(passport_code=product.passport_code, result="verified").first():
        db.session.add(VerificationLog(product_id=product.id, passport_code=product.passport_code, result="verified", ip_address="127.0.0.1", user_agent="TracePass Demo"))

    db.session.commit()
    print("Demo dataset ready.")
    print("Admin: admin@tracepass.demo / Demo1234!")
    print("Manufacturer: manufacturer@tracepass.demo / Demo1234!")
    print("Auditor: auditor@tracepass.demo / Demo1234!")
    print("Demo passport: TP-DEMO2026")
