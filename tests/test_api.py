# TracePass code note: This module implements the tests/test_api.py part of the application.
from app.extensions import db
from app.models.organization import Organization
from app.models.product import Product, STATUS_PUBLISHED
from app.models.role import Role
from app.models.user import User


# Code explanation: Authenticate the submitted credentials and create the Flask-Login session.
def login(client, email, password):
    return client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)


# Code explanation: Implement the `test health` operation used by this part of TracePass.
def test_health(client):
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'ok'


# Code explanation: Implement the `test products api returns pagination` operation used by this part of TracePass.
def test_products_api_requires_authentication(client):
    response = client.get('/api/v1/products?page=1&per_page=10')
    assert response.status_code == 401


# Code explanation: Implement the `test products api returns pagination` operation used by this part of TracePass.
def test_products_api_returns_pagination(client, app):
    with app.app_context():
        role = Role.query.filter_by(name='admin').first()
        user = User(name='API Test Admin', email='apiadmin@example.com', role_id=role.id)
        user.set_password('TestPass123!')
        db.session.add(user)
        db.session.commit()
    login(client, 'apiadmin@example.com', 'TestPass123!')
    response = client.get('/api/v1/products?page=1&per_page=10')
    assert response.status_code == 200
    data = response.get_json()
    assert {'items', 'page', 'per_page', 'pages', 'total'} <= data.keys()


# Code explanation: Implement the `test public passport hides unpublished` operation used by this part of TracePass.
def test_public_passport_hides_unpublished(client, app):
    with app.app_context():
        org = Organization(name='Test Manufacturer', type='manufacturer')
        db.session.add(org)
        db.session.flush()
        product = Product(name='Draft Shirt', manufacturer_org_id=org.id, status='draft')
        db.session.add(product)
        db.session.commit()
        code = product.passport_code
    assert client.get(f'/api/v1/public/passports/{code}').status_code == 404


# Code explanation: Implement the `test public passport published` operation used by this part of TracePass.
def test_public_passport_published(client, app):
    with app.app_context():
        org = Organization(name='Test Manufacturer', type='manufacturer')
        db.session.add(org)
        db.session.flush()
        product = Product(name='Published Shirt', manufacturer_org_id=org.id, status=STATUS_PUBLISHED, compliance_status='compliant')
        db.session.add(product)
        db.session.commit()
        code = product.passport_code
    response = client.get(f'/api/v1/public/passports/{code}')
    assert response.status_code == 200
    assert response.get_json()['passport_code'] == code
    assert response.get_json()['public_view'] is True


# Code explanation: Implement the `test report requires login` operation used by this part of TracePass.
def test_report_requires_login(client):
    response = client.get('/api/v1/reports/summary')
    assert response.status_code == 401
