from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    role = db.relationship("Role", back_populates="users")
    organization = db.relationship("Organization", back_populates="users")

    # --- password handling ---
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # Note: UserMixin provides a default `is_active` property, but since this
    # class defines `is_active` as a db.Column directly in the class body,
    # Python resolves that first — the column wins automatically, no override needed.

    # --- convenience helpers used throughout the app ---
    def has_role(self, *role_names: str) -> bool:
        return self.role is not None and self.role.name in role_names

    def __repr__(self):
        return f"<User {self.email}>"
