# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
from app.extensions import db


# What this code does: Defines the Supplier class, grouping related data and behavior used by this part of the application.
class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    material_categories_supplied = db.Column(db.String(255), nullable=True)  # comma-separated
    rating = db.Column(db.Float, nullable=True)

    organization = db.relationship("Organization")
    material_links = db.relationship("ProductMaterial", back_populates="supplier", lazy="dynamic")
    material_offerings = db.relationship("SupplierMaterial", back_populates="supplier", cascade="all, delete-orphan", lazy="dynamic")

    # What this code does: Implements the   repr   logic used by this part of the TracePass application.
    def __repr__(self):
        return f"<Supplier org_id={self.organization_id}>"
