# TracePass code note: This module implements the tests/conftest.py part of the application.
import pytest
from app import create_app
from app.extensions import db
from app.models.role import Role, ALL_ROLES
from app.models.user import User


# Code explanation: Implement the `app` operation used by this part of TracePass.
@pytest.fixture()
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        for name in ALL_ROLES:
            db.session.add(Role(name=name, permissions=''))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


# Code explanation: Implement the `client` operation used by this part of TracePass.
@pytest.fixture()
def client(app):
    return app.test_client()


# Code explanation: Implement the `admin` operation used by this part of TracePass.
@pytest.fixture()
def admin(app):
    with app.app_context():
        role = Role.query.filter_by(name='admin').first()
        user = User(name='Test Admin', email='admin@example.com', role_id=role.id)
        user.set_password('TestPass123!')
        db.session.add(user)
        db.session.commit()
        return user
