# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
import random
import string
import json
from datetime import datetime, timezone

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.decorators import role_required
from app.models.role import (
    ROLE_ADMIN, ROLE_SUPPLIER, ROLE_RETAILER, ROLE_DISTRIBUTOR, ROLE_MANUFACTURER,
)
from app.models.organization import Organization
from app.models.product import Product, STATUS_PUBLISHED, ProductBatch
from app.models.material import Material
from app.models.supplier import Supplier
from app.models.supplier_material import SupplierMaterial
from app.models.purchase_order import (
    PurchaseOrder, PO_REQUESTED, PO_CONFIRMED, PO_REJECTED, PO_PREPARING,
    PO_READY, PO_SHIPPED, PO_IN_TRANSIT, PO_DELIVERED, PO_RECEIVED, PO_CANCELLED,
)
from app.models.shipment import Shipment, SHIPMENT_IN_TRANSIT, SHIPMENT_DELIVERED
from app.models.supply_chain_event import SupplyChainEvent
from app.models.notification import Notification, NOTIF_PO_UPDATE
from app.models.purchase_order_offer import PurchaseOrderOffer, OFFER_PROPOSED, OFFER_ACCEPTED, OFFER_REJECTED, OFFER_SUPERSEDED
from app.models.user import User
from app.partners.forms import (
    PurchaseOrderForm, PurchaseOrderResponseForm, ShipmentFromPOForm,
    ConfirmReceiptForm, SupplierMaterialForm, PurchaseOrderOfferForm,
)

partners_bp = Blueprint("partners", __name__, template_folder="../templates/partners")

CAN_VIEW_PO = (ROLE_ADMIN, ROLE_SUPPLIER, ROLE_MANUFACTURER, ROLE_DISTRIBUTOR, ROLE_RETAILER)
CAN_REQUEST_PO = (ROLE_ADMIN, ROLE_MANUFACTURER, ROLE_DISTRIBUTOR, ROLE_RETAILER)
CAN_FULFILL_PO = (ROLE_ADMIN, ROLE_SUPPLIER, ROLE_MANUFACTURER, ROLE_DISTRIBUTOR)


# What this code does: Generates po number from the available project data.
def _generate_po_number():
    return "PO-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


# What this code does: Implements the  notify org logic used by this part of the TracePass application.
def _notify_org(org_id, message, product_id=None):
    if not org_id:
        return
    users = User.query.filter_by(organization_id=org_id, is_active=True).all()
    for user in users:
        db.session.add(Notification(
            user_id=user.id,
            notif_type=NOTIF_PO_UPDATE,
            message=message[:255],
            product_id=product_id,
        ))


# What this code does: Implements the  record po event logic used by this part of the TracePass application.
def _record_po_event(po, event_type, user, note):
    if not po.product_id:
        return
    db.session.add(SupplyChainEvent(
        product_id=po.product_id,
        organization_id=user.organization_id,
        event_type=event_type,
        event_date=datetime.now(timezone.utc),
        notes=note,
        recorded_by_user_id=user.id,
    ))


# What this code does: Implements the  allowed fulfillers for buyer logic used by this part of the TracePass application.
def _allowed_fulfillers_for_buyer():
    if current_user.has_role(ROLE_MANUFACTURER):
        # A manufacturer procures raw materials from suppliers.
        return Organization.query.filter(
            Organization.type == "supplier",
            Organization.is_verified.is_(True),
        ).order_by(Organization.name).all()
    if current_user.has_role(ROLE_DISTRIBUTOR, ROLE_RETAILER):
        # Downstream partners replenish finished goods from manufacturer/distributor.
        return Organization.query.filter(
            Organization.type.in_(["manufacturer", "distributor"]),
            Organization.is_verified.is_(True),
        ).order_by(Organization.name).all()
    return Organization.query.filter_by(is_verified=True).order_by(Organization.name).all()


# What this code does: Implements the my materials logic used by this part of the TracePass application.
@partners_bp.route("/partners/my-materials", methods=["GET", "POST"])
@login_required
@role_required(ROLE_SUPPLIER)
def my_materials():
    supplier = Supplier.query.filter_by(organization_id=current_user.organization_id).first()
    if supplier is None:
        supplier = Supplier(organization_id=current_user.organization_id)
        db.session.add(supplier)
        db.session.commit()

    form = SupplierMaterialForm()
    form.material_id.choices = [(m.id, f"{m.name} ({m.category or 'Material'})") for m in Material.query.order_by(Material.name).all()]
    if not form.material_id.choices:
        flash("No raw materials have been configured by the administrator yet.", "warning")
        return render_template("partners/my_materials.html", form=form, supplier=supplier, offerings=supplier.material_offerings.order_by(SupplierMaterial.created_at.desc()).all())

    if form.validate_on_submit():
        offering = SupplierMaterial.query.filter_by(supplier_id=supplier.id, material_id=form.material_id.data).first()
        if offering is None:
            offering = SupplierMaterial(supplier_id=supplier.id, material_id=form.material_id.data)
            db.session.add(offering)
        offering.unit = form.unit.data.strip().upper()
        offering.minimum_order_qty = form.minimum_order_qty.data
        offering.lead_time_days = form.lead_time_days.data
        offering.is_active = bool(form.is_active.data)
        # Keep the legacy profile field synchronized for compatibility with Phase 2/admin screens.
        names = [o.material.name for o in supplier.material_offerings.filter(SupplierMaterial.is_active.is_(True)).all()]
        if offering.material and offering.is_active and offering.material.name not in names:
            names.append(offering.material.name)
        supplier.material_categories_supplied = ", ".join(sorted(set(names)))[:255] or None
        db.session.commit()
        flash(f"{offering.material.name} is now listed as a material you trade.", "success")
        return redirect(url_for("partners.my_materials"))

    return render_template("partners/my_materials.html", form=form, supplier=supplier, offerings=supplier.material_offerings.order_by(SupplierMaterial.created_at.desc()).all())


# What this code does: Implements the toggle material offering logic used by this part of the TracePass application.
@partners_bp.route("/partners/my-materials/<int:offering_id>/toggle", methods=["POST"])
@login_required
@role_required(ROLE_SUPPLIER)
def toggle_material_offering(offering_id):
    supplier = Supplier.query.filter_by(organization_id=current_user.organization_id).first_or_404()
    offering = SupplierMaterial.query.filter_by(id=offering_id, supplier_id=supplier.id).first_or_404()
    offering.is_active = not offering.is_active
    active_names = [o.material.name for o in supplier.material_offerings.filter(SupplierMaterial.is_active.is_(True)).all()]
    supplier.material_categories_supplied = ", ".join(sorted(set(active_names)))[:255] or None
    db.session.commit()
    flash(f"{offering.material.name} is {'available' if offering.is_active else 'no longer available'} for new orders.", "info")
    return redirect(url_for("partners.my_materials"))


# What this code does: Builds and returns a list of purchase orders for the current feature.
@partners_bp.route("/partners/purchase-orders")
@login_required
@role_required(*CAN_VIEW_PO)
def list_purchase_orders():
    org_id = current_user.organization_id
    if current_user.has_role(ROLE_ADMIN):
        pos = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).all()
    else:
        pos = PurchaseOrder.query.filter(
            db.or_(PurchaseOrder.from_org_id == org_id, PurchaseOrder.to_org_id == org_id)
        ).order_by(PurchaseOrder.created_at.desc()).all()

    response_forms = {}
    receipt_forms = {}
    offer_forms = {}
    shipment_forms = {}
    for po in pos:
        if po.to_org_id == org_id or current_user.has_role(ROLE_ADMIN):
            response_forms[po.id] = PurchaseOrderResponseForm()
        if po.from_org_id == org_id or current_user.has_role(ROLE_ADMIN):
            receipt_forms[po.id] = ConfirmReceiptForm()
        if (po.from_org_id == org_id or po.to_org_id == org_id or current_user.has_role(ROLE_ADMIN)) and po.status in {PO_REQUESTED, PO_CONFIRMED}:
            offer_forms[po.id] = PurchaseOrderOfferForm()

    return render_template(
        "partners/purchase_orders.html",
        purchase_orders=pos,
        org_id=org_id,
        response_forms=response_forms,
        receipt_forms=receipt_forms,
        offer_forms=offer_forms,
        shipment_forms=shipment_forms,
        po_statuses=[PO_REQUESTED, PO_CONFIRMED, PO_REJECTED, PO_PREPARING, PO_READY, PO_SHIPPED, PO_IN_TRANSIT, PO_DELIVERED, PO_RECEIVED, PO_CANCELLED],
    )


# What this code does: Implements the partner operations logic used by this part of the TracePass application.
@partners_bp.route("/partners/operations")
@login_required
@role_required(ROLE_ADMIN, ROLE_DISTRIBUTOR, ROLE_RETAILER)
def partner_operations():
    """Dedicated downstream operations view for receiving and outbound traceability."""
    org_id = current_user.organization_id
    if current_user.has_role(ROLE_ADMIN):
        incoming = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).limit(50).all()
        outgoing = incoming
    else:
        incoming = PurchaseOrder.query.filter_by(to_org_id=org_id).order_by(PurchaseOrder.created_at.desc()).limit(50).all()
        outgoing = PurchaseOrder.query.filter_by(from_org_id=org_id).order_by(PurchaseOrder.created_at.desc()).limit(50).all()
    receipt_forms = {po.id: ConfirmReceiptForm() for po in incoming if po.status == PO_DELIVERED}
    return render_template("partners/operations.html", incoming=incoming, outgoing=outgoing, receipt_forms=receipt_forms, org_id=org_id)


# What this code does: Implements the new purchase order logic used by this part of the TracePass application.
@partners_bp.route("/partners/purchase-orders/new", methods=["GET", "POST"])
@login_required
@role_required(*CAN_REQUEST_PO)
def new_purchase_order():
    if not current_user.organization_id and not current_user.has_role(ROLE_ADMIN):
        flash("Your account isn't linked to an organization — contact an admin.", "danger")
        return redirect(url_for("partners.list_purchase_orders"))

    form = PurchaseOrderForm()
    form.product_id.choices = [
        (p.id, f"{p.name} ({p.passport_code})")
        for p in Product.query.filter_by(status=STATUS_PUBLISHED).order_by(Product.name).all()
    ]
    # Manufacturers order raw materials; show only suppliers that actively trade
    # the selected material. For downstream finished-goods orders, no material is required.
    materials = Material.query.order_by(Material.name).all()
    supplier_map = {}
    if current_user.has_role(ROLE_MANUFACTURER):
        form.material_id.choices = [(m.id, f"{m.name} ({m.category or 'Material'})") for m in materials]
        fulfillers = _allowed_fulfillers_for_buyer()
        form.to_org_id.choices = [(o.id, f"{o.name} ({o.type.title()})") for o in fulfillers]
        active_offerings = SupplierMaterial.query.join(Supplier).join(Material).filter(
            SupplierMaterial.is_active.is_(True),
            SupplierMaterial.supplier_id == Supplier.id,
            SupplierMaterial.material_id == Material.id,
        ).all()
        for offering in active_offerings:
            supplier_map.setdefault(str(offering.material_id), []).append(offering.supplier.organization_id)
    else:
        form.material_id.choices = [(0, "— Finished goods / no raw material —")] + [(m.id, f"{m.name} ({m.category or 'Material'})") for m in materials]
        form.to_org_id.choices = [(o.id, f"{o.name} ({o.type.title()})") for o in _allowed_fulfillers_for_buyer()]

    if not form.product_id.choices:
        flash("No published products are available to link to this procurement request yet.", "warning")
        return redirect(url_for("partners.list_purchase_orders"))
    if not form.to_org_id.choices:
        flash("No verified supplier/fulfilling organizations are available yet.", "warning")
        return redirect(url_for("partners.list_purchase_orders"))

    if form.validate_on_submit():
        # Manufacturer procurement is explicitly a raw-material request.
        if current_user.has_role(ROLE_MANUFACTURER) and not form.material_id.data:
            flash("A manufacturer purchase order must specify the raw material being procured.", "danger")
            return render_template("partners/purchase_order_form.html", form=form, raw_material_required=True, supplier_map=json.dumps(supplier_map))

        target = Organization.query.get(form.to_org_id.data)
        if target is None or not target.is_verified:
            abort(400)
        if current_user.has_role(ROLE_MANUFACTURER):
            if target.type != "supplier":
                abort(403)
            supplier = Supplier.query.filter_by(organization_id=target.id).first()
            offering = SupplierMaterial.query.filter_by(
                supplier_id=supplier.id if supplier else -1,
                material_id=form.material_id.data,
                is_active=True,
            ).first()
            if offering is None:
                flash("The selected supplier does not trade the selected raw material. Choose a supplier shown for that material.", "danger")
                return render_template("partners/purchase_order_form.html", form=form, raw_material_required=True, supplier_map=json.dumps(supplier_map))
            if offering.minimum_order_qty is not None and form.quantity.data < offering.minimum_order_qty:
                flash(f"The supplier's minimum order quantity is {offering.minimum_order_qty:g} {offering.unit}.", "danger")
                return render_template("partners/purchase_order_form.html", form=form, raw_material_required=True, supplier_map=json.dumps(supplier_map))

        po = PurchaseOrder(
            po_number=_generate_po_number(),
            product_id=form.product_id.data,
            material_id=form.material_id.data or None,
            from_org_id=current_user.organization_id,
            to_org_id=target.id,
            quantity=form.quantity.data,
            requested_delivery_date=form.requested_delivery_date.data,
            requested_by_user_id=current_user.id,
            notes=form.notes.data,
            status=PO_REQUESTED,
        )
        db.session.add(po)
        db.session.flush()
        _notify_org(target.id, f"New purchase order {po.po_number} from {current_user.organization.name if current_user.organization else 'buyer'} requires a price offer.", po.product_id)
        db.session.commit()
        flash(f"Purchase order {po.po_number} submitted to {target.name}.", "success")
        return redirect(url_for("partners.list_purchase_orders"))

    return render_template("partners/purchase_order_form.html", form=form, raw_material_required=current_user.has_role(ROLE_MANUFACTURER), supplier_map=json.dumps(supplier_map))


# What this code does: Implements the submit purchase order offer logic used by this part of the TracePass application.
@partners_bp.route("/partners/purchase-orders/<int:po_id>/offer", methods=["POST"])
@login_required
@role_required(*CAN_FULFILL_PO, ROLE_MANUFACTURER, ROLE_DISTRIBUTOR, ROLE_RETAILER)
def submit_purchase_order_offer(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    if not current_user.has_role(ROLE_ADMIN) and current_user.organization_id not in {po.from_org_id, po.to_org_id}:
        abort(403)
    if po.status not in {PO_REQUESTED, PO_CONFIRMED}:
        flash("This purchase order is no longer open for negotiation.", "warning")
        return redirect(url_for("partners.list_purchase_orders"))
    form = PurchaseOrderOfferForm()
    if not form.validate_on_submit():
        flash("Please enter a valid proposed unit price.", "danger")
        return redirect(url_for("partners.list_purchase_orders"))
    qty = po.confirmed_quantity or po.quantity
    if qty <= 0:
        abort(400)
    # Never allow a user to accept or create an offer against their own side only.
    for old in po.offers:
        if old.status == OFFER_PROPOSED:
            old.status = OFFER_SUPERSEDED
    offer = PurchaseOrderOffer(
        purchase_order_id=po.id,
        offered_by_user_id=current_user.id,
        unit_price=form.unit_price.data,
        currency="PKR",
        quantity=qty,
        total_price=form.unit_price.data * qty,
        confirmed_supply_date=form.confirmed_supply_date.data,
        expected_delivery_date=form.expected_delivery_date.data,
        note=form.note.data,
        status=OFFER_PROPOSED,
    )
    db.session.add(offer)
    # A counter-offer does not confirm the PO; the order remains under negotiation.
    po.status = PO_REQUESTED
    recipient_org_id = po.to_org_id if current_user.organization_id == po.from_org_id else po.from_org_id
    _notify_org(recipient_org_id, f"New price offer/counter-offer for {po.po_number}: PKR {form.unit_price.data:g}/unit for {qty} units.", po.product_id)
    db.session.commit()
    flash(f"Offer of PKR {form.unit_price.data:g} per unit submitted.", "success")
    return redirect(url_for("partners.list_purchase_orders"))


# What this code does: Implements the accept purchase order offer logic used by this part of the TracePass application.
@partners_bp.route("/partners/purchase-orders/<int:po_id>/offer/accept", methods=["POST"])
@login_required
@role_required(ROLE_ADMIN, ROLE_MANUFACTURER, ROLE_SUPPLIER, ROLE_DISTRIBUTOR, ROLE_RETAILER)
def accept_purchase_order_offer(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    if not current_user.has_role(ROLE_ADMIN) and current_user.organization_id not in {po.from_org_id, po.to_org_id}:
        abort(403)
    offer = PurchaseOrderOffer.query.filter_by(purchase_order_id=po.id, status=OFFER_PROPOSED).order_by(PurchaseOrderOffer.created_at.desc()).first()
    if offer is None:
        flash("There is no active offer to accept.", "warning")
        return redirect(url_for("partners.list_purchase_orders"))
    if not current_user.has_role(ROLE_ADMIN) and offer.offered_by.organization_id == current_user.organization_id:
        flash("You cannot accept your own offer. The other party must accept it.", "warning")
        return redirect(url_for("partners.list_purchase_orders"))
    offer.status = OFFER_ACCEPTED
    for old in po.offers:
        if old.id != offer.id and old.status == OFFER_PROPOSED:
            old.status = OFFER_SUPERSEDED
    po.agreed_unit_price = offer.unit_price
    po.agreed_total_price = offer.total_price
    po.agreed_currency = offer.currency
    po.confirmed_quantity = offer.quantity
    po.confirmed_supply_date = offer.confirmed_supply_date
    po.expected_delivery_date = offer.expected_delivery_date or po.requested_delivery_date
    po.status = PO_CONFIRMED
    po.responded_by_user_id = current_user.id
    po.responded_at = datetime.now(timezone.utc)
    po.supplier_notes = offer.note
    recipient_org_id = po.to_org_id if current_user.organization_id == po.from_org_id else po.from_org_id
    _notify_org(recipient_org_id, f"Price agreement reached for {po.po_number}: PKR {offer.unit_price:g}/unit, total PKR {offer.total_price:g}.", po.product_id)
    _record_po_event(po, "other", current_user, f"Negotiated price agreed for {po.po_number}: PKR {offer.unit_price:g}/unit × {offer.quantity} = PKR {offer.total_price:g}.")
    db.session.commit()
    flash(f"Offer accepted. Agreed price: PKR {offer.unit_price:g}/unit; total PKR {offer.total_price:g}.", "success")
    return redirect(url_for("partners.list_purchase_orders"))


# What this code does: Implements the respond to purchase order logic used by this part of the TracePass application.
@partners_bp.route("/partners/purchase-orders/<int:po_id>/respond", methods=["POST"])
@login_required
@role_required(*CAN_FULFILL_PO)
def respond_to_purchase_order(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    if not current_user.has_role(ROLE_ADMIN) and po.to_org_id != current_user.organization_id:
        abort(403)
    if po.status != PO_REQUESTED:
        flash("This purchase order is no longer awaiting a supplier response.", "warning")
        return redirect(url_for("partners.list_purchase_orders"))

    form = PurchaseOrderResponseForm()
    if form.validate_on_submit():
        now = datetime.now(timezone.utc)
        po.responded_by_user_id = current_user.id
        po.responded_at = now
        po.supplier_notes = form.supplier_notes.data

        if form.action.data == "reject":
            po.status = PO_REJECTED
            po.rejection_reason = form.supplier_notes.data or "Supplier rejected the purchase order."
            _notify_org(po.from_org_id, f"Purchase order {po.po_number} was rejected by {po.to_org.name}.", po.product_id)
        else:
            flash("Commercial acceptance now requires a negotiated price offer. Use the price negotiation controls on the purchase order.", "warning")
            return redirect(url_for("partners.list_purchase_orders"))

        db.session.commit()
        flash(f"Purchase order {po.po_number} response recorded.", "success")
    else:
        flash("Please provide a valid supplier response.", "danger")
    return redirect(url_for("partners.list_purchase_orders"))


# What this code does: Implements the prepare purchase order logic used by this part of the TracePass application.
@partners_bp.route("/partners/purchase-orders/<int:po_id>/preparing", methods=["POST"])
@login_required
@role_required(*CAN_FULFILL_PO)
def prepare_purchase_order(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    if not current_user.has_role(ROLE_ADMIN) and po.to_org_id != current_user.organization_id:
        abort(403)
    if po.status != PO_CONFIRMED:
        flash("Only an accepted purchase order can be moved to Preparing.", "warning")
        return redirect(url_for("partners.list_purchase_orders"))
    po.status = PO_PREPARING
    _notify_org(po.from_org_id, f"Purchase order {po.po_number} is now being prepared by {po.to_org.name}.", po.product_id)
    db.session.commit()
    return redirect(url_for("partners.list_purchase_orders"))


# What this code does: Implements the ready purchase order logic used by this part of the TracePass application.
@partners_bp.route("/partners/purchase-orders/<int:po_id>/ready", methods=["POST"])
@login_required
@role_required(*CAN_FULFILL_PO)
def ready_purchase_order(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    if not current_user.has_role(ROLE_ADMIN) and po.to_org_id != current_user.organization_id:
        abort(403)
    if po.status != PO_PREPARING:
        flash("Only a purchase order being prepared can be marked Ready for Dispatch.", "warning")
        return redirect(url_for("partners.list_purchase_orders"))
    po.status = PO_READY
    _notify_org(po.from_org_id, f"Purchase order {po.po_number} is ready for dispatch.", po.product_id)
    db.session.commit()
    return redirect(url_for("partners.list_purchase_orders"))


# What this code does: Implements the dispatch purchase order logic used by this part of the TracePass application.
@partners_bp.route("/partners/purchase-orders/<int:po_id>/dispatch", methods=["GET", "POST"])
@login_required
@role_required(*CAN_FULFILL_PO)
def dispatch_purchase_order(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    if not current_user.has_role(ROLE_ADMIN) and po.to_org_id != current_user.organization_id:
        abort(403)
    if po.status not in {PO_CONFIRMED, PO_PREPARING, PO_READY}:
        flash("This purchase order is not ready to be dispatched.", "warning")
        return redirect(url_for("partners.list_purchase_orders"))

    form = ShipmentFromPOForm()
    batches = ProductBatch.query.filter_by(product_id=po.product_id).order_by(ProductBatch.manufacture_date.desc()).all() if po.product_id else []
    form.batch_id.choices = [(0, "— No manufacturing batch yet —")] + [(b.id, b.batch_no) for b in batches]

    if form.validate_on_submit():
        qty = po.confirmed_quantity or po.quantity
        shipment = Shipment(
            purchase_order_id=po.id,
            batch_id=form.batch_id.data or None,
            material_id=po.material_id,
            quantity=qty,
            from_org_id=po.to_org_id,
            to_org_id=po.from_org_id,
            tracking_no=form.tracking_no.data.strip() if form.tracking_no.data else None,
            status=SHIPMENT_IN_TRANSIT,
            shipped_date=form.shipped_date.data,
            expected_delivery_date=form.expected_delivery_date.data or po.expected_delivery_date,
        )
        po.status = PO_SHIPPED
        po.dispatched_at = datetime.now(timezone.utc)
        po.expected_delivery_date = shipment.expected_delivery_date
        db.session.add(shipment)
        db.session.flush()
        _record_po_event(po, "shipped", current_user, f"Raw-material shipment {shipment.tracking_no or shipment.id} dispatched for {po.po_number}. Quantity: {qty}.")
        _notify_org(po.from_org_id, f"Purchase order {po.po_number} has been dispatched. Tracking: {shipment.tracking_no or 'not provided'}.", po.product_id)
        db.session.commit()
        flash(f"Shipment {shipment.tracking_no or shipment.id} dispatched.", "success")
        return redirect(url_for("partners.list_purchase_orders"))

    return render_template("partners/shipment_form.html", form=form, po=po)


# What this code does: Implements the deliver purchase order logic used by this part of the TracePass application.
@partners_bp.route("/partners/purchase-orders/<int:po_id>/deliver", methods=["POST"])
@login_required
@role_required(*CAN_FULFILL_PO)
def deliver_purchase_order(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    if not current_user.has_role(ROLE_ADMIN) and po.to_org_id != current_user.organization_id:
        abort(403)
    shipment = po.shipments.order_by(Shipment.created_at.desc()).first()
    if shipment is None or shipment.status != SHIPMENT_IN_TRANSIT:
        flash("No in-transit shipment is available to mark as delivered.", "warning")
        return redirect(url_for("partners.list_purchase_orders"))

    shipment.status = SHIPMENT_DELIVERED
    shipment.received_date = shipment.expected_delivery_date or datetime.now(timezone.utc).date()
    po.status = PO_DELIVERED
    po.delivered_at = datetime.now(timezone.utc)
    _record_po_event(po, "delivered", current_user, f"Shipment {shipment.tracking_no or shipment.id} delivered to {po.from_org.name} for purchase order {po.po_number}. Awaiting buyer receipt confirmation.")
    _notify_org(po.from_org_id, f"Purchase order {po.po_number} shipment has been delivered. Please confirm receipt.", po.product_id)
    db.session.commit()
    flash(f"Shipment {shipment.tracking_no or shipment.id} marked delivered.", "success")
    return redirect(url_for("partners.list_purchase_orders"))


# What this code does: Implements the receive purchase order logic used by this part of the TracePass application.
@partners_bp.route("/partners/purchase-orders/<int:po_id>/receive", methods=["POST"])
@login_required
def receive_purchase_order(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    if not current_user.has_role(ROLE_ADMIN) and po.from_org_id != current_user.organization_id:
        abort(403)
    if po.status != PO_DELIVERED:
        flash("The supplier must mark the shipment delivered before receipt can be confirmed.", "warning")
        return redirect(url_for("partners.list_purchase_orders"))

    form = ConfirmReceiptForm()
    if form.validate_on_submit():
        expected = po.confirmed_quantity or po.quantity
        if form.received_quantity.data > expected:
            flash(f"Received quantity cannot exceed the confirmed quantity ({expected}).", "danger")
            return redirect(url_for("partners.list_purchase_orders"))
        po.status = PO_RECEIVED
        po.received_at = datetime.now(timezone.utc)
        shipment = po.shipments.order_by(Shipment.created_at.desc()).first()
        if shipment:
            shipment.received_date = form.received_date.data
        _record_po_event(po, "received", current_user, f"Buyer confirmed receipt of {form.received_quantity.data} units for purchase order {po.po_number}. {form.notes.data or ''}")
        _notify_org(po.to_org_id, f"Purchase order {po.po_number} receipt was confirmed by {po.from_org.name}.", po.product_id)
        db.session.commit()
        flash(f"Purchase order {po.po_number} is now closed as Received.", "success")
    else:
        flash("Please provide a valid receipt quantity and date.", "danger")
    return redirect(url_for("partners.list_purchase_orders"))
