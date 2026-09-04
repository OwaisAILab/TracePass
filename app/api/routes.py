# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
from datetime import date, datetime, timezone
from functools import wraps

from flask import jsonify, request, current_app
from flask_login import current_user
from sqlalchemy import or_

from app.api import api_bp
from app.extensions import db
from app.models.product import Product, ProductBatch, ProductMaterial, STATUS_PUBLISHED
from app.models.organization import Organization
from app.models.product_category import ProductCategory
from app.models.supplier import Supplier
from app.models.compliance import ComplianceReview, ComplianceCheck
from app.models.recall_incident import Recall, Incident
from app.models.lifecycle import LifecycleEvent
from app.models.shipment import Shipment
from app.models.verification import VerificationLog


# What this code does: Implements the json error logic used by this part of the TracePass application.
def json_error(message, status=400, details=None):
    payload = {'error': message}
    if details:
        payload['details'] = details
    return jsonify(payload), status


# What this code does: Protects an API endpoint by requiring an authenticated user before the endpoint logic runs.
def api_login_required(fn):
    # What this code does: Implements the wrapped logic used by this part of the TracePass application.
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return json_error('Authentication required', 401)
        if not current_user.is_active:
            return json_error('Account is inactive', 403)
        return fn(*args, **kwargs)
    return wrapped


# What this code does: Implements the api roles logic used by this part of the TracePass application.
def api_roles(*roles):
    # What this code does: Implements the decorator logic used by this part of the TracePass application.
    def decorator(fn):
        # What this code does: Implements the wrapped logic used by this part of the TracePass application.
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not current_user.has_role(*roles):
                return json_error('Insufficient permissions', 403)
            return fn(*args, **kwargs)
        return wrapped
    return decorator


# What this code does: Implements the api product allowed logic used by this part of the TracePass application.
def api_product_allowed(product):
    """Enforce organization-aware access to internal product APIs."""
    if current_user.has_role('admin', 'auditor'):
        return True
    org_id = current_user.organization_id
    if not org_id:
        return False
    if current_user.has_role('manufacturer'):
        return product.manufacturer_org_id == org_id
    if current_user.has_role('supplier'):
        return any(m.supplier and m.supplier.organization_id == org_id for m in product.materials)
    if current_user.has_role('distributor', 'retailer'):
        return any(s.from_org_id == org_id or s.to_org_id == org_id for b in product.batches for s in b.shipments)
    return False


# What this code does: Implements the product json logic used by this part of the TracePass application.
def product_json(product):
    return {
        'id': product.id,
        'passport_code': product.passport_code,
        'name': product.name,
        'category': product.category_ref.name if product.category_ref else product.category,
        'brand': product.brand,
        'model': product.model,
        'description': product.description,
        'manufacturer_org_id': product.manufacturer_org_id,
        'status': product.status,
        'compliance_status': product.compliance_status,
        'image_url': product.image_url,
        'created_at': product.created_at.isoformat() if product.created_at else None,
    }


# What this code does: Implements the health logic used by this part of the TracePass application.
@api_bp.get('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'TracePass API', 'version': 'v1'})


# What this code does: Implements the products logic used by this part of the TracePass application.
@api_bp.get('/products')
@api_login_required
def products():
    query = Product.query
    q = request.args.get('q', '').strip()
    status = request.args.get('status')
    category = request.args.get('category')
    page = max(request.args.get('page', 1, type=int), 1)
    per_page = min(max(request.args.get('per_page', 20, type=int), 1), 100)

    if q:
        like = f'%{q}%'
        query = query.filter(or_(Product.name.ilike(like), Product.passport_code.ilike(like), Product.brand.ilike(like)))
    if status:
        query = query.filter(Product.status == status)
    if category:
        query = query.outerjoin(ProductCategory).filter(
            or_(Product.category == category, ProductCategory.name == category)
        )
    if current_user.has_role('manufacturer') and current_user.organization_id:
        query = query.filter(Product.manufacturer_org_id == current_user.organization_id)
    elif current_user.has_role('supplier') and current_user.organization_id:
        query = query.filter(Product.materials.any(ProductMaterial.supplier.has(Supplier.organization_id == current_user.organization_id)))
    elif current_user.has_role('distributor', 'retailer') and current_user.organization_id:
        query = query.filter(Product.batches.any(ProductBatch.shipments.any(or_(Shipment.from_org_id == current_user.organization_id, Shipment.to_org_id == current_user.organization_id))))
    elif not current_user.has_role('admin', 'auditor'):
        return json_error('Insufficient permissions', 403)

    result = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'items': [product_json(p) for p in result.items],
        'page': result.page,
        'per_page': result.per_page,
        'pages': result.pages,
        'total': result.total,
    })


# What this code does: Implements the product logic used by this part of the TracePass application.
@api_bp.get('/products/<passport_code>')
@api_login_required
def product(passport_code):
    item = Product.query.filter_by(passport_code=passport_code).first()
    if not item:
        return json_error('Product passport not found', 404)
    if not api_product_allowed(item):
        return json_error('Insufficient permissions', 403)
    return jsonify(product_json(item))


# What this code does: Implements the public passport logic used by this part of the TracePass application.
@api_bp.get('/public/passports/<passport_code>')
def public_passport(passport_code):
    item = Product.query.filter_by(passport_code=passport_code, status=STATUS_PUBLISHED).first()
    if not item:
        return json_error('Published passport not found', 404)

    # Record this as an actual verification event (same log the public HTML
    # scanner writes to) instead of just stamping the current request time —
    # 'verified_at' below is now the real timestamp of a stored event, not a
    # freshly-generated clock value with no record behind it.
    log = VerificationLog(
        product_id=item.id, passport_code=item.passport_code, result="verified",
        ip_address=request.remote_addr,
        user_agent=(request.user_agent.string[:500] if request.user_agent else None),
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({
        'passport_code': item.passport_code,
        'name': item.name,
        'category': item.category_ref.name if item.category_ref else item.category,
        'brand': item.brand,
        'model': item.model,
        'description': item.description,
        'compliance_status': item.compliance_status,
        'manufacturer': item.manufacturer.name if item.manufacturer else None,
        'verified_at': log.verified_at.isoformat(),
        'public_view': True,
        'sustainability_data': item.sustainability_data,
        'attributes': item.get_attribute_values(),
        'batches': [{'batch_no': b.batch_no, 'manufacture_date': b.manufacture_date.isoformat() if b.manufacture_date else None,
                     'production_location': b.production_location, 'quantity': b.quantity} for b in item.batches],
        'materials': [{'name': m.material.name, 'origin_country': m.material.origin_country, 'percentage': m.percentage} for m in item.materials],
        'lifecycle_events': [{'event_type': e.event_type, 'event_date': e.event_date.isoformat() if e.event_date else None,
                              'organization': e.organization.name if e.organization else None, 'location': e.location} for e in sorted(item.lifecycle_events.all(), key=lambda x: x.event_date)],
        'supply_chain_events': [{'event_type': e.event_type, 'event_date': e.event_date.isoformat() if e.event_date else None,
                                'organization': e.organization.name if e.organization else None, 'location': e.location} for e in sorted(item.supply_chain_events.all(), key=lambda x: x.event_date)],
    })


# What this code does: Implements the report summary logic used by this part of the TracePass application.
@api_bp.get('/reports/summary')
@api_login_required
@api_roles('admin', 'auditor')
def report_summary():
    total = Product.query.count()
    published = Product.query.filter_by(status=STATUS_PUBLISHED).count()
    compliant = Product.query.filter_by(compliance_status='compliant').count()
    non_compliant = Product.query.filter_by(compliance_status='non_compliant').count()
    pending_reviews = ComplianceReview.query.filter_by(decision='corrections_requested').count()
    open_recalls = Recall.query.filter(Recall.status != 'closed').count()
    open_incidents = Incident.query.filter(Incident.status != 'resolved').count()
    return jsonify({
        'products': {'total': total, 'published': published, 'compliant': compliant, 'non_compliant': non_compliant},
        'compliance_rate_percent': round((compliant / total) * 100, 2) if total else 0,
        'pending_corrections': pending_reviews,
        'open_recalls': open_recalls,
        'open_incidents': open_incidents,
        'generated_at': date.today().isoformat(),
    })


# What this code does: Implements the api 404 logic used by this part of the TracePass application.
@api_bp.errorhandler(404)
def api_404(_):
    return json_error('API endpoint not found', 404)
