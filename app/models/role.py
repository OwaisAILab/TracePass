
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


# Defines the role class and groups its related data and behavior.
class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    permissions = db.Column(db.String(255), nullable=True)  # comma-separated or JSON string

    users = db.relationship("User", back_populates="role", lazy="dynamic")

# Provides the internal repr helper used by this module's workflow.
    def __repr__(self):
        return f"<Role {self.name}>"
