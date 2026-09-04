# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
from datetime import datetime, timezone
from app.extensions import db


# What this code does: Defines the SupplierMaterial class, grouping related data and behavior used by this part of the application.
class SupplierMaterial(db.Model):
    __tablename__ = "supplier_materials"

    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey("materials.id"), nullable=False)
    unit = db.Column(db.String(30), nullable=False, default="KG")
    minimum_order_qty = db.Column(db.Float, nullable=True)
    lead_time_days = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    supplier = db.relationship("Supplier", back_populates="material_offerings")
    material = db.relationship("Material")

    __table_args__ = (db.UniqueConstraint("supplier_id", "material_id", name="uq_supplier_material"),)

    # What this code does: Implements the   repr   logic used by this part of the TracePass application.
    def __repr__(self):
        return f"<SupplierMaterial supplier={self.supplier_id} material={self.material_id}>"
