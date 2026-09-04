# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app, send_from_directory
from flask_login import login_required, current_user
import os
import uuid
import json
from werkzeug.utils import secure_filename

from app.extensions import db
from app.decorators import role_required
from app.models.role import (
    ROLE_ADMIN, ROLE_SUPPLIER, ROLE_MANUFACTURER, ROLE_DISTRIBUTOR, ROLE_RETAILER, ROLE_AUDITOR
)
from app.models.organization import Organization
from app.models.material import Material
from app.models.product_category import ProductCategory
from app.models.product_template import ProductTemplate, TemplateField
from app.models.industry import Industry
from app.models.supplier import Supplier
from app.models.product import (
    Product,
    ProductBatch,
    ProductMaterial,
    QRCode,
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    STATUS_ARCHIVED,
    PRODUCT_STATUSES,
)
from app.models.supply_chain_event import SupplyChainEvent
from app.models.shipment import Shipment
from app.models.purchase_order import PurchaseOrder
from app.models.certificate import Certificate, Document
from app.models.compliance import ComplianceCheck, ComplianceReview
from app.models.lifecycle import LifecycleEvent
from app.models.verification import VerificationLog
from app.tracepass.forms import ProductForm, BatchForm, MaterialLinkForm, EventForm, ShipmentForm, LifecycleEventForm
from app.tracepass.utils import generate_qr_for_passport_code, qr_image_url, build_product_timeline
from app.uploads import validate_upload

tracepass_bp = Blueprint("tracepass", __name__, template_folder="../templates/tracepass")

CAN_MANAGE_PASSPORTS = (ROLE_ADMIN, ROLE_MANUFACTURER)
CAN_TRACE_SUPPLY_CHAIN = (ROLE_ADMIN, ROLE_SUPPLIER, ROLE_MANUFACTURER, ROLE_DISTRIBUTOR, ROLE_RETAILER, ROLE_AUDITOR)



# What this code does: Implements the  save product image logic used by this part of the TracePass application.
def _save_product_image(file_storage):
    """Save a product image and return its browser-accessible relative URL."""
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "product_images")
    os.makedirs(upload_dir, exist_ok=True)
    original = secure_filename(file_storage.filename or "product_image")
    ext = os.path.splitext(original)[1].lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    file_storage.save(os.path.join(upload_dir, filename))
    return f"/uploads/product_images/{filename}"


# What this code does: Removes product image after checking that the operation is allowed.
def _delete_product_image(image_url):
    """Delete a locally uploaded product image, but never delete external URLs."""
    prefix = "/uploads/product_images/"
    if not image_url or not image_url.startswith(prefix):
        return
    filename = os.path.basename(image_url)
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], "product_images", filename)
    try:
        if os.path.isfile(filepath):
            os.remove(filepath)
    except OSError:
        pass


# What this code does: Implements the product image logic used by this part of the TracePass application.
@tracepass_bp.route("/uploads/product_images/<path:filename>")
def product_image(filename):
    """Serve product images used by the public Digital Product Passport."""
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "product_images")
    return send_from_directory(upload_dir, filename)

# What this code does: Implements the  manufacturer choices logic used by this part of the TracePass application.
def _manufacturer_choices():
    query = Organization.query.filter_by(type="manufacturer")
    if current_user.has_role(ROLE_MANUFACTURER) and current_user.organization_id:
        query = query.filter_by(id=current_user.organization_id)
    orgs = query.order_by(Organization.name).all()
    return [(o.id, o.name) for o in orgs]


# --- internal passport list/detail/create/edit -----------------------------

# What this code does: Builds and returns a list of products for the current feature.
@tracepass_bp.route("/products")
@login_required
def list_products():
    query = Product.query
    org_id = current_user.organization_id
    # Scope the list to what each partner organization is actually entitled to
    # see, at the query level — matching the same relationships enforced by
    # _authorize_product_access() for individual product pages. This avoids
    # showing a user records they couldn't open anyway (information-security
    # best practice: don't list what you'd 403 on if they clicked it).
    if current_user.has_role(ROLE_ADMIN, ROLE_AUDITOR):
        pass  # unrestricted — admins/auditors see the whole catalog
    elif current_user.has_role(ROLE_MANUFACTURER) and org_id:
        query = query.filter_by(manufacturer_org_id=org_id)
    elif current_user.has_role(ROLE_SUPPLIER) and org_id:
        supplied_product_ids = db.session.query(ProductMaterial.product_id).join(
            Supplier, ProductMaterial.supplier_id == Supplier.id
        ).filter(Supplier.organization_id == org_id)
        query = query.filter(Product.id.in_(supplied_product_ids))
    elif current_user.has_role(ROLE_DISTRIBUTOR, ROLE_RETAILER) and org_id:
        shipped_product_ids = db.session.query(ProductBatch.product_id).join(
            Shipment, Shipment.batch_id == ProductBatch.id
        ).filter(db.or_(Shipment.from_org_id == org_id, Shipment.to_org_id == org_id))
        ordered_product_ids = db.session.query(PurchaseOrder.product_id).filter(
            PurchaseOrder.product_id.isnot(None),
            db.or_(PurchaseOrder.from_org_id == org_id, PurchaseOrder.to_org_id == org_id),
        )
        query = query.filter(db.or_(
            Product.id.in_(shipped_product_ids),
            Product.id.in_(ordered_product_ids),
        ))
    elif org_id:
        # Any other authenticated-but-unrecognized role: show nothing rather
        # than defaulting open.
        query = query.filter(db.false())

    # --- search: passport code, name, brand ---
    search = request.args.get("q", "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Product.passport_code.ilike(like),
                Product.name.ilike(like),
                Product.brand.ilike(like),
            )
        )

    # --- filter: status, category ---
    status_filter = request.args.get("status", "").strip()
    if status_filter in PRODUCT_STATUSES:
        query = query.filter_by(status=status_filter)

    category_filter = request.args.get("category", "").strip()
    if category_filter:
        query = query.filter(Product.category_id == int(category_filter)) if category_filter.isdigit() else query.filter_by(category=category_filter)

    # --- pagination ---
    page = request.args.get("page", 1, type=int)
    per_page = 10
    pagination = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    # distinct categories for the filter dropdown (scoped to what's visible to this user)
    categories = ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.name).all()

    return render_template(
        "tracepass/products.html",
        products=pagination.items,
        pagination=pagination,
        search=search,
        status_filter=status_filter,
        category_filter=category_filter,
        categories=categories,
        statuses=PRODUCT_STATUSES,
    )


# What this code does: Implements the new product logic used by this part of the TracePass application.
@tracepass_bp.route("/products/new", methods=["GET", "POST"])
@login_required
@role_required(*CAN_MANAGE_PASSPORTS)
def new_product():
    form = ProductForm()
    form.manufacturer_org_id.choices = _manufacturer_choices()
    industries = Industry.query.filter_by(is_active=True).order_by(Industry.name).all()
    categories = ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.name).all()
    form.industry_id.choices = [(0, "— All industries —")] + [(i.id, i.name) for i in industries]
    form.category_id.choices = [(c.id, f"{c.industry.name + ' — ' if c.industry else ''}{c.name}") for c in categories]

    categories_by_industry = {"0": []}
    for ind in industries:
        categories_by_industry[str(ind.id)] = []
    for c in categories:
        label = f"{c.industry.name + ' — ' if c.industry else ''}{c.name}"
        entry = {"id": c.id, "name": label}
        categories_by_industry["0"].append(entry)
        if c.industry_id:
            categories_by_industry.setdefault(str(c.industry_id), []).append(entry)

    selected_category = ProductCategory.query.get(request.form.get("category_id", type=int)) if request.method == "POST" else None
    template_fields = (
        selected_category.template.fields
        if selected_category and selected_category.template and selected_category.template.is_active
        else []
    )

    if not form.manufacturer_org_id.choices:
        flash("No manufacturer organizations exist yet. Ask an admin to add one first.", "warning")
        return redirect(url_for("tracepass.list_products"))

    if form.validate_on_submit():
        category_obj = ProductCategory.query.get(form.category_id.data)
        if category_obj is None:
            form.category_id.errors.append("Selected category is invalid.")
            return render_template(
                "tracepass/product_form.html",
                form=form,
                template_fields=template_fields,
                selected_category=None,
                categories_by_industry=categories_by_industry,
            )
        # Optional industry filter consistency check
        if form.industry_id.data and form.industry_id.data != 0:
            if category_obj.industry_id and category_obj.industry_id != form.industry_id.data:
                form.category_id.errors.append("Selected category does not belong to the chosen industry.")
                return render_template(
                    "tracepass/product_form.html",
                    form=form,
                    template_fields=template_fields,
                    selected_category=category_obj,
                    categories_by_industry=categories_by_industry,
                )
        template_fields = (
            category_obj.template.fields
            if category_obj.template and category_obj.template.is_active
            else []
        )
        attributes = {}
        missing_attributes = []
        for field in template_fields:
            value = request.form.get(f"attr_{field.id}", "").strip()
            if field.required and not value:
                missing_attributes.append(field.label)
            if value:
                attributes[field.key] = value
        if missing_attributes:
            flash("Required template fields missing: " + ", ".join(missing_attributes), "danger")
            return render_template(
                "tracepass/product_form.html",
                form=form,
                template_fields=template_fields,
                selected_category=category_obj,
                categories_by_industry=categories_by_industry,
            )
        if form.image.data:
            validate_upload(form.image.data, {"jpg", "jpeg", "png", "webp", "avif"})
        product = Product(
            name=form.name.data.strip(),
            category_id=category_obj.id,
            category=category_obj.name,
            brand=form.brand.data.strip() if form.brand.data else None,
            model=form.model.data.strip() if form.model.data else None,
            description=form.description.data.strip() if form.description.data else None,
            manufacturer_org_id=form.manufacturer_org_id.data,
            image_url=_save_product_image(form.image.data) if form.image.data else None,
            attribute_values=json.dumps(attributes),
            sustainability_data=form.sustainability_data.data.strip() if form.sustainability_data.data else None,
            status=STATUS_DRAFT,
        )
        db.session.add(product)
        db.session.commit()
        flash(f"Passport '{product.passport_code}' created as draft.", "success")
        return redirect(url_for("tracepass.view_product", product_id=product.id))

    return render_template(
        "tracepass/product_form.html",
        form=form,
        template_fields=template_fields,
        selected_category=selected_category,
        categories_by_industry=categories_by_industry,
    )


# What this code does: Implements the edit product logic used by this part of the TracePass application.
@tracepass_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(*CAN_MANAGE_PASSPORTS)
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    _authorize_product_access(product)

    form = ProductForm(obj=product)
    form.manufacturer_org_id.choices = _manufacturer_choices()
    categories = ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.name).all()
    form.category_id.choices = [(c.id, f"{c.industry.name + ' — ' if c.industry else ''}{c.name}") for c in categories]

    if request.method == "GET" and product.category_id:
        form.category_id.data = product.category_id
    selected_category = product.category_ref
    template_fields = selected_category.template.fields if selected_category and selected_category.template and selected_category.template.is_active else []
    existing_attributes = product.get_attribute_values()

    if form.validate_on_submit():
        # Manufacturers cannot move a passport to another manufacturer.
        if current_user.has_role(ROLE_MANUFACTURER) and form.manufacturer_org_id.data != current_user.organization_id:
            abort(403)
        if form.image.data:
            validate_upload(form.image.data, {"jpg", "jpeg", "png", "webp", "avif"})
        category = ProductCategory.query.get(form.category_id.data)
        if category is None or not category.is_active:
            flash("Please select an active product category.", "danger")
            return render_template("tracepass/product_form.html", form=form, product=product, editing=True, template_fields=template_fields, existing_attributes=existing_attributes, selected_category=selected_category)

        template_fields = category.template.fields if category.template and category.template.is_active else []
        product.name = form.name.data.strip()
        product.category_id = category.id
        product.category = category.name
        product.brand = form.brand.data.strip() if form.brand.data else None
        product.model = form.model.data.strip() if form.model.data else None
        product.description = form.description.data.strip() if form.description.data else None
        product.sustainability_data = form.sustainability_data.data.strip() if form.sustainability_data.data else None
        product.manufacturer_org_id = form.manufacturer_org_id.data
        attributes = {}
        missing_attributes = []
        for field in template_fields:
            value = request.form.get(f"attr_{field.id}", "").strip()
            if field.required and not value:
                missing_attributes.append(field.label)
            if value:
                attributes[field.key] = value
        if missing_attributes:
            flash("Required template fields missing: " + ", ".join(missing_attributes), "danger")
            return render_template("tracepass/product_form.html", form=form, product=product, editing=True, template_fields=template_fields, existing_attributes=existing_attributes, selected_category=category)
        product.attribute_values = json.dumps(attributes)
        if form.image.data:
            old_image = product.image_url
            product.image_url = _save_product_image(form.image.data)
            _delete_product_image(old_image)
        db.session.commit()
        flash("Product passport updated.", "success")
        return redirect(url_for("tracepass.view_product", product_id=product.id))

    return render_template("tracepass/product_form.html", form=form, product=product, editing=True, template_fields=template_fields, existing_attributes=existing_attributes, selected_category=selected_category)


# What this code does: Implements the view product logic used by this part of the TracePass application.
@tracepass_bp.route("/products/<int:product_id>")
@login_required
def view_product(product_id):
    product = Product.query.get_or_404(product_id)
    _authorize_product_access(product)

    batch_form = BatchForm()
    material_form = MaterialLinkForm()
    material_form.material_id.choices = [(m.id, m.name) for m in Material.query.order_by(Material.name).all()]
    material_form.supplier_id.choices = [(0, "— None —")] + [
        (s.id, s.organization.name) for s in Supplier.query.join(Organization).order_by(Organization.name).all()
    ]

    event_form = EventForm()
    event_form.batch_id.choices = [(0, "— No specific batch —")] + [
        (b.id, b.batch_no) for b in product.batches
    ]

    shipment_form = ShipmentForm()
    lifecycle_form = LifecycleEventForm()
    lifecycle_form.organization_id.choices = [(0, "— Unspecified —")] + [(o.id, o.name) for o in Organization.query.order_by(Organization.name).all()]
    org_choices = [(0, "— Unspecified —")] + [(o.id, o.name) for o in Organization.query.order_by(Organization.name).all()]
    shipment_form.from_org_id.choices = org_choices
    shipment_form.to_org_id.choices = org_choices
    attribute_values = product.get_attribute_values()

    timeline = build_product_timeline(product)
    lifecycle_events = LifecycleEvent.query.filter_by(product_id=product.id).order_by(LifecycleEvent.event_date.desc()).all()

    # --- compliance context (Phase 4) ---
    from app.compliance.forms import CertificateForm, DocumentForm, ReviewForm

    cert_form = CertificateForm()
    doc_form = DocumentForm()
    review_form = ReviewForm()
    from app.compliance.forms import CertificateReviewForm

    certificates = Certificate.query.filter(
        db.or_(Certificate.product_id == product.id, Certificate.organization_id == product.manufacturer_org_id)
    ).order_by(Certificate.created_at.desc()).all()
    review_certificate_forms = {c.id: CertificateReviewForm() for c in certificates}
    documents = Document.query.filter_by(product_id=product.id).order_by(Document.uploaded_at.desc()).all()
    recent_checks = (
        ComplianceCheck.query.filter_by(product_id=product.id)
        .order_by(ComplianceCheck.checked_at.desc())
        .limit(20)
        .all()
    )
    reviews = ComplianceReview.query.filter_by(product_id=product.id).order_by(ComplianceReview.reviewed_at.desc()).all()

    from app.reporting.forms import RecallForm, IncidentForm
    recall_form = RecallForm()
    recall_form.batch_id.choices = [(0, "— Entire product —")] + [(b.id, b.batch_no) for b in product.batches]
    incident_form = IncidentForm()

    return render_template(
        "tracepass/product_detail.html",
        product=product,
        batch_form=batch_form,
        material_form=material_form,
        event_form=event_form,
        shipment_form=shipment_form,
        lifecycle_form=lifecycle_form,
        lifecycle_events=lifecycle_events,
        attribute_values=attribute_values,
        timeline=timeline,
        missing_fields=product.missing_required_fields(),
        cert_form=cert_form,
        doc_form=doc_form,
        review_form=review_form,
        certificates=certificates,
        documents=documents,
        recent_checks=recent_checks,
        reviews=reviews,
        review_certificate_forms=review_certificate_forms,
        recall_form=recall_form,
        incident_form=incident_form,
    )


# What this code does: Implements the  authorize product access logic used by this part of the TracePass application.
def _authorize_product_access(product):
    """Authorize internal passport/traceability access by supply-chain relationship."""
    if current_user.has_role(ROLE_ADMIN, ROLE_AUDITOR):
        return
    org_id = current_user.organization_id
    if not org_id:
        abort(403)
    if current_user.has_role(ROLE_MANUFACTURER) and product.manufacturer_org_id == org_id:
        return
    if current_user.has_role(ROLE_SUPPLIER) and any(m.supplier and m.supplier.organization_id == org_id for m in product.materials):
        return
    if current_user.has_role(ROLE_DISTRIBUTOR, ROLE_RETAILER):
        if any(s.from_org_id == org_id or s.to_org_id == org_id for b in product.batches for s in b.shipments):
            return
        if PurchaseOrder.query.filter(
            PurchaseOrder.product_id == product.id,
            db.or_(PurchaseOrder.from_org_id == org_id, PurchaseOrder.to_org_id == org_id)
        ).first():
            return
    abort(403)


# --- batches -----------------------------------------------------------

# What this code does: Adds batch to the relevant application or database context.
@tracepass_bp.route("/products/<int:product_id>/batches", methods=["POST"])
@login_required
@role_required(*CAN_MANAGE_PASSPORTS)
def add_batch(product_id):
    product = Product.query.get_or_404(product_id)
    # Role check above only confirms the user CAN manage passports somewhere;
    # this confirms they own THIS specific product (prevents editing another
    # manufacturer's product by guessing/changing the product_id in the URL).
    _authorize_product_access(product)
    form = BatchForm()
    if form.validate_on_submit():
        batch = ProductBatch(
            product_id=product.id,
            batch_no=form.batch_no.data.strip(),
            manufacture_date=form.manufacture_date.data,
            production_location=form.production_location.data.strip() if form.production_location.data else None,
            quantity=form.quantity.data,
        )
        db.session.add(batch)
        db.session.commit()
        flash(f"Batch '{batch.batch_no}' added.", "success")
    else:
        for field, errors in form.errors.items():
            for err in errors:
                flash(f"{field}: {err}", "danger")
    return redirect(url_for("tracepass.view_product", product_id=product.id))


# --- material linking ----------------------------------------------------

# What this code does: Implements the link material logic used by this part of the TracePass application.
@tracepass_bp.route("/products/<int:product_id>/materials", methods=["POST"])
@login_required
@role_required(*CAN_MANAGE_PASSPORTS)
def link_material(product_id):
    product = Product.query.get_or_404(product_id)
    # Ownership check — see comment in add_batch() above.
    _authorize_product_access(product)
    form = MaterialLinkForm()
    form.material_id.choices = [(m.id, m.name) for m in Material.query.all()]
    form.supplier_id.choices = [(0, "— None —")] + [
        (s.id, s.organization.name) for s in Supplier.query.join(Organization).all()
    ]

    if form.validate_on_submit():
        percentage = form.percentage.data
        current_total = product.material_percentage_total()
        if percentage is not None and current_total + percentage > 100.01:
            flash(f"Material percentages cannot exceed 100%. Current total is {current_total:g}%.", "danger")
            return redirect(url_for("tracepass.view_product", product_id=product.id))

        link = ProductMaterial(
            product_id=product.id,
            material_id=form.material_id.data,
            supplier_id=form.supplier_id.data if form.supplier_id.data else None,
            quantity=form.quantity.data,
            percentage=percentage,
        )
        db.session.add(link)
        db.session.commit()
        flash("Material linked to product.", "success")
    else:
        for field, errors in form.errors.items():
            for err in errors:
                flash(f"{field}: {err}", "danger")
    return redirect(url_for("tracepass.view_product", product_id=product.id))


# --- supply chain events --------------------------------------------------

# What this code does: Implements the log event logic used by this part of the TracePass application.
@tracepass_bp.route("/products/<int:product_id>/events", methods=["POST"])
@login_required
@role_required(*CAN_TRACE_SUPPLY_CHAIN)
def log_event(product_id):
    product = Product.query.get_or_404(product_id)
    # Partners may record events only for products in which their organization
    # has a traceability relationship. Admin/auditor may record/review globally.
    if not current_user.has_role(ROLE_ADMIN, ROLE_AUDITOR):
        allowed = current_user.has_role(ROLE_MANUFACTURER) and product.manufacturer_org_id == current_user.organization_id
        if not allowed and current_user.organization_id:
            allowed = any(
                (e.organization_id == current_user.organization_id) or
                any((m.supplier and m.supplier.organization_id == current_user.organization_id) for m in product.materials)
                for e in product.supply_chain_events.all()
            )
        if not allowed:
            abort(403)

    form = EventForm()
    form.batch_id.choices = [(0, "— No specific batch —")] + [(b.id, b.batch_no) for b in product.batches]

    if form.validate_on_submit():
        batch_id = form.batch_id.data if form.batch_id.data else None
        if batch_id and not any(b.id == batch_id for b in product.batches):
            abort(400)
        event = SupplyChainEvent(
            product_id=product.id, batch_id=batch_id,
            organization_id=current_user.organization_id,
            event_type=form.event_type.data,
            location=form.location.data.strip() if form.location.data else None,
            event_date=form.event_date.data, notes=form.notes.data,
            recorded_by_user_id=current_user.id,
        )
        db.session.add(event)
        db.session.commit()
        flash("Supply-chain event logged.", "success")
    else:
        for field, errors in form.errors.items():
            for err in errors:
                flash(f"{field}: {err}", "danger")
    return redirect(url_for("tracepass.view_product", product_id=product.id))


# --- shipments -------------------------------------------------------------

# What this code does: Adds shipment to the relevant application or database context.
@tracepass_bp.route("/batches/<int:batch_id>/shipments", methods=["POST"])
@login_required
@role_required(*CAN_TRACE_SUPPLY_CHAIN)
def add_shipment(batch_id):
    batch = ProductBatch.query.get_or_404(batch_id)
    form = ShipmentForm()
    org_choices = [(0, "— Unspecified —")] + [(o.id, f"{o.name} ({o.type})") for o in Organization.query.order_by(Organization.name).all()]
    form.from_org_id.choices = org_choices
    form.to_org_id.choices = org_choices

    if form.validate_on_submit():
        from_id = form.from_org_id.data or None
        to_id = form.to_org_id.data or None
        if not current_user.has_role(ROLE_ADMIN, ROLE_AUDITOR):
            if current_user.organization_id not in {from_id, to_id}:
                abort(403)
        if from_id and to_id and from_id == to_id:
            flash("Shipment origin and destination must be different organizations.", "danger")
            return redirect(url_for("tracepass.view_product", product_id=batch.product_id))
        shipment = Shipment(
            batch_id=batch.id, from_org_id=from_id, to_org_id=to_id,
            tracking_no=form.tracking_no.data.strip() if form.tracking_no.data else None,
            status=form.status.data, shipped_date=form.shipped_date.data,
            expected_delivery_date=form.expected_delivery_date.data, received_date=form.received_date.data,
        )
        db.session.add(shipment)
        # A shipment is itself a traceability event. This makes the timeline
        # useful even when users never manually create a separate event.
        if shipment.status in {"in_transit", "delivered"}:
            event_type = "received" if shipment.status == "delivered" else "shipped"
            event_date = shipment.received_date or shipment.shipped_date or shipment.created_at.date()
            from datetime import datetime, time
            event_dt = datetime.combine(event_date, time.min)
            db.session.add(SupplyChainEvent(
                product_id=batch.product_id, batch_id=batch.id,
                organization_id=current_user.organization_id, event_type=event_type,
                location=(shipment.to_org.name if shipment.status == "delivered" and shipment.to_org else (shipment.from_org.name if shipment.from_org else None)),
                event_date=event_dt,
                notes=f"Shipment {shipment.tracking_no or shipment.id} status: {shipment.status}.",
                recorded_by_user_id=current_user.id,
            ))
        db.session.commit()
        flash("Shipment recorded and traceability timeline updated.", "success")
    else:
        for field, errors in form.errors.items():
            for err in errors:
                flash(f"{field}: {err}", "danger")
    return redirect(url_for("tracepass.view_product", product_id=batch.product_id))

# What this code does: Adds lifecycle event to the relevant application or database context.
@tracepass_bp.route("/products/<int:product_id>/lifecycle", methods=["POST"])
@login_required
@role_required(*CAN_TRACE_SUPPLY_CHAIN)
def add_lifecycle_event(product_id):
    product = Product.query.get_or_404(product_id)
    _authorize_product_access(product)
    form = LifecycleEventForm()
    form.organization_id.choices = [(0, "— Unspecified —")] + [(o.id, o.name) for o in Organization.query.order_by(Organization.name).all()]
    if form.validate_on_submit():
        org_id = form.organization_id.data or current_user.organization_id
        if current_user.has_role(ROLE_MANUFACTURER) and org_id and org_id != current_user.organization_id:
            abort(403)
        event = LifecycleEvent(product_id=product.id, event_type=form.event_type.data,
                               event_date=form.event_date.data, organization_id=org_id,
                               location=form.location.data.strip() if form.location.data else None,
                               notes=form.notes.data.strip() if form.notes.data else None,
                               recorded_by_user_id=current_user.id)
        db.session.add(event)
        db.session.commit()
        flash("Lifecycle event recorded.", "success")
    else:
        for field, errors in form.errors.items():
            for err in errors: flash(f"{field}: {err}", "danger")
    return redirect(url_for("tracepass.view_product", product_id=product.id))

# What this code does: Implements the supply chain dashboard logic used by this part of the TracePass application.
@tracepass_bp.route("/supply-chain")
@login_required
@role_required(*CAN_TRACE_SUPPLY_CHAIN)
def supply_chain_dashboard():
    """Partner-facing traceability overview for the current organization."""
    products = Product.query.order_by(Product.created_at.desc()).all()
    if current_user.has_role(ROLE_MANUFACTURER) and current_user.organization_id:
        products = [p for p in products if p.manufacturer_org_id == current_user.organization_id]
    elif current_user.has_role(ROLE_SUPPLIER) and current_user.organization_id:
        products = [p for p in products if any(m.supplier and m.supplier.organization_id == current_user.organization_id for m in p.materials)]
    elif current_user.has_role(ROLE_DISTRIBUTOR, ROLE_RETAILER) and current_user.organization_id:
        org_id = current_user.organization_id
        products = [p for p in products if any(
            s.from_org_id == org_id or s.to_org_id == org_id
            for b in p.batches for s in b.shipments
        ) or PurchaseOrder.query.filter(
            PurchaseOrder.product_id == p.id,
            db.or_(PurchaseOrder.from_org_id == org_id, PurchaseOrder.to_org_id == org_id)
        ).first() is not None]

    rows = []
    for product in products:
        timeline = build_product_timeline(product)
        rows.append({
            "product": product,
            "event_count": product.supply_chain_events.count(),
            "shipment_count": sum(b.shipments.count() for b in product.batches),
            "last_activity": timeline[-1] if timeline else None,
        })
    return render_template("tracepass/supply_chain.html", rows=rows)


# What this code does: Implements the publish product logic used by this part of the TracePass application.
@tracepass_bp.route("/products/<int:product_id>/publish", methods=["POST"])
@login_required
@role_required(*CAN_MANAGE_PASSPORTS)
def publish_product(product_id):
    product = Product.query.get_or_404(product_id)
    # Ownership check — see comment in add_batch() above.
    _authorize_product_access(product)

    missing = product.missing_required_fields()
    if missing:
        flash(f"Cannot publish — missing required fields: {', '.join(missing)}.", "danger")
        return redirect(url_for("tracepass.view_product", product_id=product.id))

    product.status = STATUS_PUBLISHED
    db.session.commit()

    # Generate a QR code the first time a passport is published.
    if product.qr_code is None:
        code_value = generate_qr_for_passport_code(product.passport_code)
        qr = QRCode(product_id=product.id, code_value=code_value)
        db.session.add(qr)
        db.session.commit()

    flash("Passport published and QR code generated.", "success")
    return redirect(url_for("tracepass.view_product", product_id=product.id))


# What this code does: Implements the archive product logic used by this part of the TracePass application.
@tracepass_bp.route("/products/<int:product_id>/archive", methods=["POST"])
@login_required
@role_required(*CAN_MANAGE_PASSPORTS)
def archive_product(product_id):
    product = Product.query.get_or_404(product_id)
    # Ownership check — see comment in add_batch() above.
    _authorize_product_access(product)
    product.status = STATUS_ARCHIVED
    db.session.commit()
    flash("Passport archived.", "info")
    return redirect(url_for("tracepass.view_product", product_id=product.id))


# --- public verification (no login required) ------------------------------

# What this code does: Implements the verify scanner logic used by this part of the TracePass application.
@tracepass_bp.route("/verify")
def verify_scanner():
    """Public QR scanner/manual passport verification entry point."""
    return render_template("tracepass/public/verify_scanner.html")


# What this code does: Implements the verify passport logic used by this part of the TracePass application.
@tracepass_bp.route("/verify/<passport_code>")
def verify_passport(passport_code):
    product = Product.query.filter_by(passport_code=passport_code).first()
    if product is None:
        db.session.add(VerificationLog(passport_code=passport_code, result="invalid",
                                       ip_address=request.remote_addr, user_agent=request.user_agent.string[:500]))
        db.session.commit()
        return render_template("tracepass/public/not_found.html"), 404
    if product.status != STATUS_PUBLISHED:
        db.session.add(VerificationLog(product_id=product.id, passport_code=passport_code, result="unpublished",
                                       ip_address=request.remote_addr, user_agent=request.user_agent.string[:500]))
        db.session.commit()
        return render_template("tracepass/public/not_found.html"), 404

    db.session.add(VerificationLog(product_id=product.id, passport_code=passport_code, result="verified",
                                   ip_address=request.remote_addr, user_agent=request.user_agent.string[:500]))
    db.session.commit()

    # sustainability_data is stored as a raw JSON string (see demo_seed.py);
    # parse it into a dict so the template can render readable labels
    # instead of dumping the JSON text itself onto the page. Falls back to
    # the raw text if it isn't valid JSON, so nothing silently disappears.
    sustainability_parsed = None
    if product.sustainability_data:
        try:
            sustainability_parsed = json.loads(product.sustainability_data)
        except (ValueError, TypeError):
            sustainability_parsed = None

    industry_obj = product.category_ref.industry if product.category_ref and product.category_ref.industry else None

    public_data = {
        "passport_code": product.passport_code, "name": product.name,
        "industry": industry_obj.name if industry_obj else None,
        "industry_image_url": industry_obj.image_url if industry_obj else None,
        "category": product.category_ref.name if product.category_ref else product.category,
        "template": product.category_ref.template.name if product.category_ref and product.category_ref.template else None,
        "attributes": product.get_attribute_values(), "brand": product.brand, "model": product.model,
        "description": product.description, "image_url": product.image_url,
        "manufacturer_name": product.manufacturer.name if product.manufacturer else None,
        "batches": [{"batch_no": b.batch_no, "manufacture_date": b.manufacture_date,
                     "production_location": b.production_location, "quantity": b.quantity} for b in product.batches],
        "materials": [{"name": m.material.name, "origin_country": m.material.origin_country, "percentage": m.percentage} for m in product.materials],
        "compliance_status": product.compliance_status,
        "sustainability_data": product.sustainability_data,
        "sustainability": sustainability_parsed,
        "lifecycle_events": [{"event_type": e.event_type, "event_date": e.event_date, "organization": e.organization.name if e.organization else None,
                              "location": e.location, "notes": e.notes} for e in sorted(product.lifecycle_events.all(), key=lambda x: x.event_date)],
        "supply_chain_events": [{"event_type": e.event_type, "event_date": e.event_date, "organization": e.organization.name if e.organization else None,
                                 "location": e.location, "notes": e.notes} for e in sorted(product.supply_chain_events.all(), key=lambda x: x.event_date)],
    }
    return render_template("tracepass/public/passport.html", p=public_data)


# What this code does: Implements the verification history logic used by this part of the TracePass application.
@tracepass_bp.route("/verification-history")
@login_required
@role_required(ROLE_ADMIN, ROLE_AUDITOR)
def verification_history():
    query = VerificationLog.query
    search = request.args.get("q", "").strip()
    result_filter = request.args.get("result", "").strip()
    if search: query = query.filter(VerificationLog.passport_code.ilike(f"%{search}%"))
    if result_filter in {"verified", "unpublished", "invalid"}: query = query.filter_by(result=result_filter)
    page = request.args.get("page", 1, type=int)
    pagination = query.order_by(VerificationLog.verified_at.desc()).paginate(page=page, per_page=25, error_out=False)
    return render_template("reporting/verification_history.html", pagination=pagination, logs=pagination.items, search=search, result_filter=result_filter)
