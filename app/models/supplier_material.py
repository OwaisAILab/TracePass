# TracePass code note: This module implements the app/models/supplier_material.py part of the application.
from datetime import datetime, timezone
from app.extensions import db


# Code explanation: Define the Supplier Material data model or application component used by TracePass.
class SupplierMaterial(db.Model):
    __tablename__ = "supplier_materials"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `supplier_id` stores this model attribute in the SQL database.
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    # Database field: `material_id` stores this model attribute in the SQL database.
    material_id = db.Column(db.Integer, db.ForeignKey("materials.id"), nullable=False)
    # Database field: `unit` stores this model attribute in the SQL database.
    unit = db.Column(db.String(30), nullable=False, default="KG")
    # Database field: `minimum_order_qty` stores this model attribute in the SQL database.
    minimum_order_qty = db.Column(db.Float, nullable=True)
    # Database field: `lead_time_days` stores this model attribute in the SQL database.
    lead_time_days = db.Column(db.Integer, nullable=True)
    # Database field: `is_active` stores this model attribute in the SQL database.
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    # Database field: `created_at` stores this model attribute in the SQL database.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    supplier = db.relationship("Supplier", back_populates="material_offerings")
    material = db.relationship("Material")

    __table_args__ = (db.UniqueConstraint("supplier_id", "material_id", name="uq_supplier_material"),)

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<SupplierMaterial supplier={self.supplier_id} material={self.material_id}>"
