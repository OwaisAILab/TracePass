import os
import uuid

from flask import Blueprint, render_template, redirect, url_for, flash, abort, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.exceptions import HTTPException
from werkzeug.utils import secure_filename

from app.extensions import db
from app.decorators import role_required
from app.models.role import ROLE_ADMIN
from app.models.user import User
from app.models.organization import Organization, ORG_TYPES
from app.models.supplier import Supplier
from app.models.material import Material
from app.models.product_category import ProductCategory
from app.models.industry import Industry
from app.models.product_template import ProductTemplate, TemplateField
from app.models.registration_request import RegistrationRequest, REQUEST_PENDING, REQUEST_APPROVED, REQUEST_REJECTED, REQUESTABLE_ROLES
from app.models.registration_request_document import RegistrationRequestDocument
from app.models.role import Role
from app.models.notification import Notification
from app.auth.forms import AdminCreateUserForm
from app.admin.forms import OrganizationForm, SupplierForm, MaterialForm, ProductCategoryForm, IndustryForm, EditIndustryForm, ProductTemplateForm
from app.uploads import validate_upload

admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin", url_prefix="/admin")


def _save_industry_image(file_storage):
    """Save an uploaded industry image and return its browser-accessible URL."""
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "industry_images")
    os.makedirs(upload_dir, exist_ok=True)
    original = secure_filename(file_storage.filename or "industry_image")
    ext = os.path.splitext(original)[1].lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    file_storage.save(os.path.join(upload_dir, filename))
    return url_for("admin.industry_image", filename=filename)


@admin_bp.route("/uploads/industry_images/<path:filename>")
def industry_image(filename):
    """Serve uploaded industry images (used on the admin list and public landing page)."""
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "industry_images")
    return send_from_directory(upload_dir, filename)


@admin_bp.route("/users")
@login_required
@role_required(ROLE_ADMIN)
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users)


@admin_bp.route("/users/new", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def new_user():
    form = AdminCreateUserForm()
    form.organization_id.choices = [(0, "— None —")] + [
        (o.id, f"{o.name} ({o.type}) {'✓ verified' if o.is_verified else '— unverified'}")
        for o in Organization.query.order_by(Organization.name).all()
    ]
    if form.validate_on_submit():
        from app.models.role import Role
        role = Role.query.filter_by(name=form.role.data).first()
        if role is None:
            flash("Selected role is not configured.", "danger")
            return render_template("admin/user_form.html", form=form)
        user = User(name=form.name.data.strip(), email=form.email.data.lower().strip(), role_id=role.id,
                    organization_id=form.organization_id.data if form.organization_id.data else None)
        user.set_password(form.password.data)
        db.session.add(user); db.session.commit()
        flash(f"Account created for {user.email} ({role.name}). Share the temporary password securely.", "success")
        return redirect(url_for("admin.list_users"))
    return render_template("admin/user_form.html", form=form)


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@role_required(ROLE_ADMIN)
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f"{user.email} is now {'active' if user.is_active else 'deactivated'}.", "info")
    return redirect(url_for("admin.list_users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@role_required(ROLE_ADMIN)
def delete_user(user_id):
    """Permanently remove a deactivated user. Active accounts must be deactivated first."""
    from flask_login import current_user

    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("admin.list_users"))
    if user.is_active:
        flash("Deactivate the account before deleting it.", "warning")
        return redirect(url_for("admin.list_users"))
    email = user.email
    db.session.delete(user)
    db.session.commit()
    flash(f"User '{email}' has been permanently deleted.", "success")
    return redirect(url_for("admin.list_users"))


@admin_bp.route("/registration-requests")
@login_required
@role_required(ROLE_ADMIN)
def list_registration_requests():
    """List account requests submitted through the public Contact Us page."""
    requests = RegistrationRequest.query.order_by(RegistrationRequest.created_at.desc()).all()
    return render_template("admin/registration_requests.html", requests=requests)


@admin_bp.route("/registration-requests/documents/<int:document_id>")
@login_required
@role_required(ROLE_ADMIN)
def download_registration_request_document(document_id):
    """Allow administrators to inspect submitted authenticity evidence."""
    document = RegistrationRequestDocument.query.get_or_404(document_id)
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(upload_dir, document.file_path, as_attachment=True, download_name=document.original_filename)


@admin_bp.route("/registration-requests/<int:request_id>")
@login_required
@role_required(ROLE_ADMIN)
def view_registration_request(request_id):
    """Show the applicant and organization details before an admin decides."""
    item = RegistrationRequest.query.get_or_404(request_id)
    from flask_wtf import FlaskForm
    return render_template("admin/registration_request_detail.html", item=item, form=FlaskForm())


@admin_bp.route("/registration-requests/<int:request_id>/approve", methods=["POST"])
@login_required
@role_required(ROLE_ADMIN)
def approve_registration_request(request_id):
    """Verify the organization and create the requested role account."""
    from datetime import datetime, timezone
    item = RegistrationRequest.query.get_or_404(request_id)
    if item.status != REQUEST_PENDING:
        flash("This registration request has already been reviewed.", "warning")
        return redirect(url_for("admin.view_registration_request", request_id=item.id))

    if not item.authenticity_documents:
        flash("Approval is blocked because no authenticity documents were submitted.", "danger")
        return redirect(url_for("admin.view_registration_request", request_id=item.id))

    if User.query.filter_by(email=item.email).first():
        flash("An account with this email already exists. The request was not approved.", "danger")
        return redirect(url_for("admin.view_registration_request", request_id=item.id))

    role = Role.query.filter_by(name=item.requested_role).first()
    if role is None or item.requested_role not in REQUESTABLE_ROLES:
        flash("The requested role is not configured for organizational registration.", "danger")
        return redirect(url_for("admin.view_registration_request", request_id=item.id))

    organization = None
    if item.registration_no:
        organization = Organization.query.filter_by(registration_no=item.registration_no).first()
    if organization is not None and organization.type != item.organization_type:
        flash("The registration number belongs to an organization of a different type. Verify the request before approving it.", "danger")
        return redirect(url_for("admin.view_registration_request", request_id=item.id))

    if organization is None:
        organization = Organization(
            name=item.organization_name,
            type=item.organization_type,
            registration_no=item.registration_no,
            contact_email=item.organization_email,
            contact_phone=item.organization_phone or item.phone,
            address=item.address,
            is_verified=True,
        )
        db.session.add(organization)
        db.session.flush()
    else:
        organization.is_verified = True
        if item.organization_email and not organization.contact_email:
            organization.contact_email = item.organization_email
        if item.organization_phone and not organization.contact_phone:
            organization.contact_phone = item.organization_phone
        if item.address and not organization.address:
            organization.address = item.address

    user = User(
        name=item.name.strip(),
        email=item.email.lower().strip(),
        role_id=role.id,
        organization_id=organization.id,
        is_active=True,
    )
    user.password_hash = item.password_hash
    db.session.add(user)
    db.session.flush()

    item.status = REQUEST_APPROVED
    item.organization_id = organization.id
    item.created_user_id = user.id
    item.reviewed_by_id = current_user.id
    item.reviewed_at = datetime.now(timezone.utc)
    db.session.add(Notification(
        user_id=user.id,
        notif_type="account_request",
        message="Your TracePass account request has been approved. You can now log in.",
    ))
    db.session.commit()
    flash(f"Request approved. Account created for {user.email} under {organization.name}.", "success")
    return redirect(url_for("admin.list_registration_requests"))


@admin_bp.route("/registration-requests/<int:request_id>/reject", methods=["POST"])
@login_required
@role_required(ROLE_ADMIN)
def reject_registration_request(request_id):
    """Reject a request while preserving the decision and reason for auditability."""
    from datetime import datetime, timezone
    item = RegistrationRequest.query.get_or_404(request_id)
    if item.status != REQUEST_PENDING:
        flash("This registration request has already been reviewed.", "warning")
        return redirect(url_for("admin.view_registration_request", request_id=item.id))
    reason = (request.form.get("rejection_reason") or "").strip()
    if not reason:
        flash("Please provide a rejection reason.", "danger")
        return redirect(url_for("admin.view_registration_request", request_id=item.id))
    item.status = REQUEST_REJECTED
    item.rejection_reason = reason[:500]
    item.reviewed_by_id = current_user.id
    item.reviewed_at = datetime.now(timezone.utc)
    db.session.commit()
    flash("Registration request rejected.", "info")
    return redirect(url_for("admin.list_registration_requests"))


@admin_bp.route("/organizations")
@login_required
@role_required(ROLE_ADMIN)
def list_organizations():
    organizations = Organization.query.order_by(Organization.name).all()
    return render_template("admin/organizations.html", organizations=organizations)


@admin_bp.route("/organizations/new", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def new_organization():
    form = OrganizationForm()
    if form.validate_on_submit():
        existing_registration = (
            Organization.query.filter_by(registration_no=form.registration_no.data).first()
            if form.registration_no.data else None
        )
        if existing_registration:
            form.registration_no.errors.append("Registration number already exists.")
        else:
            org = Organization(name=form.name.data.strip(), type=form.type.data,
                               registration_no=form.registration_no.data.strip() if form.registration_no.data else None,
                               contact_email=form.contact_email.data.strip().lower() if form.contact_email.data else None,
                               contact_phone=form.contact_phone.data.strip() if form.contact_phone.data else None,
                               address=form.address.data.strip() if form.address.data else None)
            db.session.add(org); db.session.commit()
            flash(f"Organization '{org.name}' created.", "success")
            return redirect(url_for("admin.list_organizations"))
    return render_template("admin/organization_form.html", form=form)


@admin_bp.route("/organizations/<int:org_id>/verify", methods=["POST"])
@login_required
@role_required(ROLE_ADMIN)
def verify_organization(org_id):
    org = Organization.query.get_or_404(org_id)
    org.is_verified = True
    db.session.commit()
    flash(f"'{org.name}' marked as verified.", "success")
    return redirect(url_for("admin.list_organizations"))


@admin_bp.route("/suppliers")
@login_required
@role_required(ROLE_ADMIN)
def list_suppliers():
    suppliers = Supplier.query.join(Organization).order_by(Organization.name).all()
    return render_template("admin/suppliers.html", suppliers=suppliers)


@admin_bp.route("/suppliers/new", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def new_supplier():
    form = SupplierForm()
    orgs = Organization.query.filter_by(type="supplier").order_by(Organization.name).all()
    form.organization_id.choices = [(o.id, f"{o.name}{' ✓' if o.is_verified else ' — unverified'}") for o in orgs]
    if form.validate_on_submit():
        if Supplier.query.filter_by(organization_id=form.organization_id.data).first():
            form.organization_id.errors.append("This organization already has a supplier profile.")
        else:
            supplier = Supplier(organization_id=form.organization_id.data,
                                material_categories_supplied=form.material_categories_supplied.data.strip() if form.material_categories_supplied.data else None,
                                rating=form.rating.data)
            db.session.add(supplier); db.session.commit()
            flash("Supplier profile created.", "success")
            return redirect(url_for("admin.list_suppliers"))
    return render_template("admin/supplier_form.html", form=form)


@admin_bp.route("/materials")
@login_required
@role_required(ROLE_ADMIN)
def list_materials():
    materials = Material.query.order_by(Material.name).all()
    return render_template("admin/materials.html", materials=materials)


@admin_bp.route("/materials/new", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def new_material():
    form = MaterialForm()
    if form.validate_on_submit():
        material = Material(name=form.name.data.strip(), category=form.category.data.strip() if form.category.data else None,
                            origin_country=form.origin_country.data.strip() if form.origin_country.data else None,
                            sustainability_notes=form.sustainability_notes.data.strip() if form.sustainability_notes.data else None)
        db.session.add(material); db.session.commit()
        flash(f"Material '{material.name}' created.", "success")
        return redirect(url_for("admin.list_materials"))
    return render_template("admin/material_form.html", form=form)


@admin_bp.route("/categories")
@login_required
@role_required(ROLE_ADMIN)
def list_categories():
    categories = ProductCategory.query.order_by(ProductCategory.name).all()
    return render_template("admin/categories.html", categories=categories)


@admin_bp.route("/industries")
@login_required
@role_required(ROLE_ADMIN)
def list_industries():
    industries = Industry.query.order_by(Industry.name).all()
    return render_template("admin/industries.html", industries=industries)


@admin_bp.route("/industries/new", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def new_industry():
    form = IndustryForm()
    if form.validate_on_submit():
        if Industry.query.filter_by(name=form.name.data.strip()).first():
            form.name.errors.append("Industry already exists.")
        else:
            try:
                validate_upload(form.image.data, {"jpg", "jpeg", "png", "webp", "avif"})
            except HTTPException as e:
                form.image.errors.append(e.description or "That file couldn't be uploaded. Try a different image.")
            else:
                image_url = _save_industry_image(form.image.data)
                obj = Industry(
                    name=form.name.data.strip(),
                    description=form.description.data.strip() if form.description.data else None,
                    image_url=image_url,
                    is_active=form.is_active.data,
                )
                db.session.add(obj); db.session.commit()
                flash(f"Industry '{obj.name}' created.", "success")
                return redirect(url_for("admin.list_industries"))
    return render_template("admin/industry_form.html", form=form)


def _delete_industry_image(image_url):
    """Delete a locally uploaded industry image, but never delete bundled/static or external images."""
    prefix = "/admin/uploads/industry_images/"
    if not image_url or not image_url.startswith(prefix):
        return
    filename = os.path.basename(image_url)
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], "industry_images", filename)
    try:
        if os.path.isfile(filepath):
            os.remove(filepath)
    except OSError:
        pass


@admin_bp.route("/industries/<int:industry_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def edit_industry(industry_id):
    industry = Industry.query.get_or_404(industry_id)
    form = EditIndustryForm(obj=industry)
    if form.validate_on_submit():
        existing = Industry.query.filter_by(name=form.name.data.strip()).first()
        if existing and existing.id != industry.id:
            form.name.errors.append("Industry already exists.")
        else:
            image_error = False
            if form.image.data:
                try:
                    validate_upload(form.image.data, {"jpg", "jpeg", "png", "webp"})
                except HTTPException as e:
                    form.image.errors.append(e.description or "That file couldn't be uploaded. Try a different image.")
                    image_error = True
            if not image_error:
                industry.name = form.name.data.strip()
                industry.description = form.description.data.strip() if form.description.data else None
                industry.is_active = form.is_active.data
                if form.image.data:
                    old_image_url = industry.image_url
                    industry.image_url = _save_industry_image(form.image.data)
                    _delete_industry_image(old_image_url)
                db.session.commit()
                flash(f"Industry '{industry.name}' updated.", "success")
                return redirect(url_for("admin.list_industries"))
    return render_template("admin/industry_form.html", form=form, industry=industry)


@admin_bp.route("/industries/<int:industry_id>/delete", methods=["POST"])
@login_required
@role_required(ROLE_ADMIN)
def delete_industry(industry_id):
    """Delete an industry only when it has no linked categories or templates."""
    industry = Industry.query.get_or_404(industry_id)
    cat_count = len(industry.categories) if industry.categories is not None else 0
    tpl_count = len(industry.templates) if industry.templates is not None else 0
    if cat_count or tpl_count:
        flash(
            f"Cannot delete '{industry.name}': it still has {cat_count} categor{'y' if cat_count == 1 else 'ies'} "
            f"and {tpl_count} template{'s' if tpl_count != 1 else ''}. Reassign or remove them first.",
            "warning",
        )
        return redirect(url_for("admin.list_industries"))
    name = industry.name
    _delete_industry_image(industry.image_url)
    db.session.delete(industry)
    db.session.commit()
    flash(f"Industry '{name}' deleted.", "success")
    return redirect(url_for("admin.list_industries"))


@admin_bp.route("/templates")
@login_required
@role_required(ROLE_ADMIN)
def list_templates():
    templates = ProductTemplate.query.order_by(ProductTemplate.name).all()
    return render_template("admin/templates.html", templates=templates)


@admin_bp.route("/templates/new", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def new_template():
    form = ProductTemplateForm()
    industries = Industry.query.filter_by(is_active=True).order_by(Industry.name).all()
    categories = ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.name).all()
    form.industry_id.choices = [(i.id, i.name) for i in industries]
    form.category_id.choices = [(0, "— No category assignment —")] + [(c.id, c.name) for c in categories]
    if form.validate_on_submit():
        template = ProductTemplate(name=form.name.data.strip(), industry_id=form.industry_id.data, description=form.description.data.strip() if form.description.data else None, is_active=form.is_active.data)
        db.session.add(template); db.session.flush()
        if form.fields_definition.data:
            for idx, line in enumerate(form.fields_definition.data.splitlines()):
                parts = [p.strip() for p in line.split("|", 4)]
                if len(parts) < 4 or not parts[0] or not parts[1]:
                    continue
                key, label, field_type, required = parts[:4]
                help_text = parts[4] if len(parts) == 5 else None
                if field_type not in {"text", "number", "date", "textarea"}: field_type = "text"
                db.session.add(TemplateField(template_id=template.id, key=key, label=label, field_type=field_type, required=required.lower() in {"1","true","yes","required"}, help_text=help_text, sort_order=idx))
        category_id = form.category_id.data or None
        if category_id:
            category = ProductCategory.query.get(category_id)
            if category:
                category.template_id = template.id
                category.industry_id = template.industry_id
        db.session.commit()
        flash(f"Product template '{template.name}' created.", "success")
        return redirect(url_for("admin.list_templates"))
    return render_template("admin/template_form.html", form=form)


@admin_bp.route("/categories/new", methods=["GET", "POST"])
@login_required
@role_required(ROLE_ADMIN)
def new_category():
    form = ProductCategoryForm()
    industries = Industry.query.filter_by(is_active=True).order_by(Industry.name).all()
    all_categories = ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.name).all()

    form.industry_id.choices = [(0, "— No industry —")] + [(i.id, i.name) for i in industries]
    form.parent_id.choices = [(0, "— Top-level category —")] + [(c.id, c.name) for c in all_categories]

    # Build industry → parent options map for the cascading UI (JS).
    # Key "0" = categories with no industry (or show none when industry is unset).
    categories_by_industry = {"0": []}
    for ind in industries:
        categories_by_industry[str(ind.id)] = []
    for c in all_categories:
        key = str(c.industry_id) if c.industry_id else "0"
        categories_by_industry.setdefault(key, []).append({"id": c.id, "name": c.name})

    if form.validate_on_submit():
        parent_id = form.parent_id.data or None
        industry_id = form.industry_id.data or None
        if parent_id == 0:
            parent_id = None
        if industry_id == 0:
            industry_id = None

        # Enforce parent belongs to the same industry (or parent has no industry).
        if parent_id:
            parent = ProductCategory.query.get(parent_id)
            if parent is None:
                form.parent_id.errors.append("Selected parent category does not exist.")
            elif industry_id and parent.industry_id and parent.industry_id != industry_id:
                form.parent_id.errors.append(
                    "Parent category must belong to the same industry (or have no industry)."
                )

        if not form.parent_id.errors:
            category = ProductCategory(
                name=form.name.data.strip(),
                description=form.description.data.strip() if form.description.data else None,
                parent_id=parent_id,
                industry_id=industry_id,
                is_active=form.is_active.data,
            )
            db.session.add(category)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                form.name.errors.append("A category with this name already exists.")
            else:
                flash(f"Category '{category.name}' created.", "success")
                return redirect(url_for("admin.list_categories"))

    return render_template(
        "admin/category_form.html",
        form=form,
        categories_by_industry=categories_by_industry,
    )
