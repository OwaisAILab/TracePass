import pytest
from app import create_app
from app.extensions import db
from app.models.role import Role, ALL_ROLES
from app.models.user import User


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


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin(app):
    with app.app_context():
        role = Role.query.filter_by(name='admin').first()
        user = User(name='Test Admin', email='admin@example.com', role_id=role.id)
        user.set_password('TestPass123!')
        db.session.add(user)
        db.session.commit()
        return user
