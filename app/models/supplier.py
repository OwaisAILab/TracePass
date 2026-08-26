# TracePass code note: This module implements the app/models/supplier.py part of the application.
from app.extensions import db


# Code explanation: Define the Supplier data model or application component used by TracePass.
class Supplier(db.Model):
    __tablename__ = "suppliers"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `organization_id` stores this model attribute in the SQL database.
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    # Database field: `material_categories_supplied` stores this model attribute in the SQL database.
    material_categories_supplied = db.Column(db.String(255), nullable=True)  # comma-separated
    # Database field: `rating` stores this model attribute in the SQL database.
    rating = db.Column(db.Float, nullable=True)

    organization = db.relationship("Organization")
    material_links = db.relationship("ProductMaterial", back_populates="supplier", lazy="dynamic")
    material_offerings = db.relationship("SupplierMaterial", back_populates="supplier", cascade="all, delete-orphan", lazy="dynamic")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<Supplier org_id={self.organization_id}>"
