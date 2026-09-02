from app.extensions import db


class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    material_categories_supplied = db.Column(db.String(255), nullable=True)  # comma-separated
    rating = db.Column(db.Float, nullable=True)

    organization = db.relationship("Organization")
    material_links = db.relationship("ProductMaterial", back_populates="supplier", lazy="dynamic")
    material_offerings = db.relationship("SupplierMaterial", back_populates="supplier", cascade="all, delete-orphan", lazy="dynamic")

    def __repr__(self):
        return f"<Supplier org_id={self.organization_id}>"
