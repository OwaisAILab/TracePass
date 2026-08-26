# TracePass code note: This module implements the app/models/user.py part of the application.
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


# Code explanation: Define the User data model or application component used by TracePass.
class User(UserMixin, db.Model):
    __tablename__ = "users"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `name` stores this model attribute in the SQL database.
    name = db.Column(db.String(120), nullable=False)
    # Database field: `email` stores this model attribute in the SQL database.
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    # Database field: `password_hash` stores this model attribute in the SQL database.
    password_hash = db.Column(db.String(255), nullable=False)
    # Database field: `role_id` stores this model attribute in the SQL database.
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    # Database field: `organization_id` stores this model attribute in the SQL database.
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)
    # Database field: `is_active` stores this model attribute in the SQL database.
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    # Database field: `created_at` stores this model attribute in the SQL database.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    role = db.relationship("Role", back_populates="users")
    organization = db.relationship("Organization", back_populates="users")

    # --- password handling ---
    # Code explanation: Convert a plain-text password into a secure password hash before storing it.
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    # Code explanation: Compare a supplied password with the stored secure hash during authentication.
    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # Note: UserMixin provides a default `is_active` property, but since this
    # class defines `is_active` as a db.Column directly in the class body,
    # Python resolves that first — the column wins automatically, no override needed.

    # --- convenience helpers used throughout the app ---
    # Code explanation: Provide a reusable role check used by routes and templates to control access and navigation.
    def has_role(self, *role_names: str) -> bool:
        return self.role is not None and self.role.name in role_names

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<User {self.email}>"
