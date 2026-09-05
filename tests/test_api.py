
from app.extensions import db
from app.models.organization import Organization
from app.models.product import Product, STATUS_PUBLISHED
from app.models.role import Role
from app.models.user import User


#  Handles user authentication by validating credentials and creating a secure logged-in session.
def login(client, email, password):
    return client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)


#  Automated test that verifies the expected behavior of health.
def test_health(client):
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'ok'


#  Automated test that verifies the expected behavior of products api returns pagination.
def test_products_api_returns_pagination(client):
    response = client.get('/api/v1/products?page=1&per_page=10')
    assert response.status_code == 200
    data = response.get_json()
    assert {'items', 'page', 'per_page', 'pages', 'total'} <= data.keys()


#  Automated test that verifies the expected behavior of public passport hides unpublished.
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


#  Automated test that verifies the expected behavior of public passport published.
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


#  Automated test that verifies the expected behavior of report requires login.
def test_report_requires_login(client):
    response = client.get('/api/v1/reports/summary')
    assert response.status_code == 401
