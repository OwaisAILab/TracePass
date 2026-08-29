import random
import string
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.decorators import role_required
from app.models.role import ROLE_CUSTOMER
from app.models.product import Product, ProductBatch, STATUS_PUBLISHED
from app.models.industry import Industry
from app.models.product_category import ProductCategory
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem, ORDER_PAID
from app.models.complaint import Complaint
from app.models.supply_chain_event import SupplyChainEvent
from app.shop.forms import AddToCartForm, CheckoutForm, ComplaintForm

shop_bp = Blueprint("shop", __name__, template_folder="../templates/shop")


def _get_or_create_cart():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if cart is None:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    return cart


def _generate_order_number():
    return "ORD-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


# --- public storefront -------------------------------------------------------

@shop_bp.route("/store")
def landing():
    featured = (
        Product.query.filter(Product.status == STATUS_PUBLISHED, Product.price.isnot(None))
        .order_by(Product.created_at.desc())
        .limit(6)
        .all()
    )
    industries = Industry.query.filter_by(is_active=True).order_by(Industry.name).all()
    categories = ProductCategory.query.filter_by(is_active=True).order_by(ProductCategory.name).limit(12).all()
    return render_template("shop/landing.html", featured=featured, industries=industries, categories=categories)


@shop_bp.route("/verify")
def verify_scanner():
    """Public QR scanner/manual passport verification page."""
    return render_template("shop/verify_scanner.html")


@shop_bp.route("/shop")
def catalog():
    products = (
        Product.query.filter(Product.status == STATUS_PUBLISHED, Product.price.isnot(None))
        .order_by(Product.created_at.desc())
        .all()
    )
    return render_template("shop/catalog.html", products=products)


@shop_bp.route("/shop/<passport_code>")
def product_page(passport_code):
    product = Product.query.filter_by(passport_code=passport_code).first_or_404()
    if not product.is_purchasable():
        abort(404)
    cart_form = AddToCartForm()
    return render_template("shop/product_page.html", product=product, cart_form=cart_form)


# --- cart --------------------------------------------------------------------

@shop_bp.route("/cart/add/<int:product_id>", methods=["POST"])
@login_required
@role_required(ROLE_CUSTOMER)
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    if not product.is_purchasable():
        flash("This item isn't available for purchase.", "danger")
        return redirect(url_for("shop.catalog"))

    form = AddToCartForm()
    if form.validate_on_submit():
        cart = _get_or_create_cart()
        existing = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
        if existing:
            existing.quantity += form.quantity.data
        else:
            db.session.add(CartItem(cart_id=cart.id, product_id=product.id, quantity=form.quantity.data))
        db.session.commit()
        flash(f"Added {product.name} to your cart.", "success")
    else:
        flash("Couldn't add that to your cart — check the quantity.", "danger")
    return redirect(url_for("shop.product_page", passport_code=product.passport_code))


@shop_bp.route("/cart")
@login_required
@role_required(ROLE_CUSTOMER)
def view_cart():
    cart = _get_or_create_cart()
    return render_template("shop/cart.html", cart=cart)


@shop_bp.route("/cart/update/<int:item_id>", methods=["POST"])
@login_required
@role_required(ROLE_CUSTOMER)
def update_cart_item(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.cart.user_id != current_user.id:
        abort(403)
    try:
        qty = int(request.form.get("quantity", 1))
    except ValueError:
        qty = 1
    if qty <= 0:
        db.session.delete(item)
    else:
        item.quantity = min(qty, 20)
    db.session.commit()
    return redirect(url_for("shop.view_cart"))


@shop_bp.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
@role_required(ROLE_CUSTOMER)
def remove_cart_item(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.cart.user_id != current_user.id:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("shop.view_cart"))


# --- checkout (mock) -----------------------------------------------------------

@shop_bp.route("/checkout", methods=["GET", "POST"])
@login_required
@role_required(ROLE_CUSTOMER)
def checkout():
    cart = _get_or_create_cart()
    if not cart.items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("shop.catalog"))

    # Re-verify every item is still purchasable at checkout time — a product
    # could have been pulled from sale since it was added to the cart.
    unavailable = [item for item in cart.items if not item.product.is_purchasable()]
    if unavailable:
        names = ", ".join(i.product.name for i in unavailable)
        flash(f"Some items in your cart are no longer available: {names}. Please remove them to continue.", "danger")
        return redirect(url_for("shop.view_cart"))

    form = CheckoutForm()
    if form.validate_on_submit():
        order = Order(
            order_number=_generate_order_number(),
            customer_id=current_user.id,
            status=ORDER_PAID,  # mock payment "succeeds" immediately
            shipping_name=form.shipping_name.data.strip(),
            shipping_address=form.shipping_address.data.strip(),
            payment_last4=form.card_last4.data,
            total_amount=cart.total(),
        )
        db.session.add(order)
        db.session.flush()  # get order.id before creating items

        for item in cart.items:
            db.session.add(OrderItem(
                order_id=order.id, product_id=item.product_id,
                quantity=item.quantity, unit_price=item.product.price,
            ))
            # The consumer purchase is the final commercial traceability event.
            batch = item.product.batches[0] if item.product.batches else None
            db.session.add(SupplyChainEvent(
                product_id=item.product_id,
                batch_id=batch.id if batch else None,
                organization_id=None, event_type="sold",
                location=form.shipping_address.data.strip(),
                event_date=datetime.now(timezone.utc),
                notes=f"Customer order {order.order_number}; quantity {item.quantity}.",
                recorded_by_user_id=current_user.id,
            ))
            db.session.delete(item)

        db.session.commit()
        flash(f"Order {order.order_number} placed! (This is a demo checkout — no real payment was processed.)", "success")
        return redirect(url_for("shop.order_detail", order_id=order.id))

    return render_template("shop/checkout.html", cart=cart, form=form)


# --- order history -----------------------------------------------------------

@shop_bp.route("/orders")
@login_required
@role_required(ROLE_CUSTOMER)
def order_history():
    orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("shop/order_history.html", orders=orders)


@shop_bp.route("/orders/<int:order_id>")
@login_required
@role_required(ROLE_CUSTOMER)
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.customer_id != current_user.id:
        abort(403)
    return render_template("shop/order_detail.html", order=order)


# --- public complaint / return request (no login required) ---------------------

@shop_bp.route("/verify/<passport_code>/complaint", methods=["POST"])
def submit_complaint(passport_code):
    product = Product.query.filter_by(passport_code=passport_code).first_or_404()
    if product.status != STATUS_PUBLISHED:
        abort(404)

    form = ComplaintForm()
    if form.validate_on_submit():
        complaint = Complaint(
            product_id=product.id,
            complaint_type=form.complaint_type.data,
            email=form.email.data.strip().lower(),
            order_reference=form.order_reference.data.strip() if form.order_reference.data else None,
            description=form.description.data,
        )
        db.session.add(complaint)
        db.session.commit()
        flash("Your request has been submitted. We'll follow up by email.", "success")
    else:
        for field, errors in form.errors.items():
            for err in errors:
                flash(f"{field}: {err}", "danger")
    return redirect(url_for("tracepass.verify_passport", passport_code=passport_code))
