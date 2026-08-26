# TracePass code note: This module implements the app/models/role.py part of the application.
from app.extensions import db

# Fixed role set per spec section 4. Used by seed.py and by decorators.py
# for readable role checks (ROLE_CUSTOMER instead of magic strings).
ROLE_CUSTOMER = "customer"
ROLE_SUPPLIER = "supplier"
ROLE_MANUFACTURER = "manufacturer"
ROLE_DISTRIBUTOR = "distributor"
ROLE_RETAILER = "retailer"
ROLE_AUDITOR = "auditor"
ROLE_ADMIN = "admin"

ALL_ROLES = [
    ROLE_CUSTOMER,
    ROLE_SUPPLIER,
    ROLE_MANUFACTURER,
    ROLE_DISTRIBUTOR,
    ROLE_RETAILER,
    ROLE_AUDITOR,
    ROLE_ADMIN,
]


# Code explanation: Define the Role data model or application component used by TracePass.
class Role(db.Model):
    __tablename__ = "roles"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `name` stores this model attribute in the SQL database.
    name = db.Column(db.String(50), unique=True, nullable=False)
    # Database field: `permissions` stores this model attribute in the SQL database.
    permissions = db.Column(db.String(255), nullable=True)  # comma-separated or JSON string

    users = db.relationship("User", back_populates="role", lazy="dynamic")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<Role {self.name}>"
