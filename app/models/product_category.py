# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
from datetime import datetime, timezone
from app.extensions import db


# What this code does: Defines the ProductCategory class, grouping related data and behavior used by this part of the application.
class ProductCategory(db.Model):
    __tablename__ = "product_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    industry_id = db.Column(db.Integer, db.ForeignKey("industries.id"), nullable=True, index=True)
    template_id = db.Column(db.Integer, db.ForeignKey("product_templates.id"), nullable=True, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("product_categories.id"), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    parent = db.relationship("ProductCategory", remote_side=[id], backref=db.backref("children", lazy="dynamic"))
    industry = db.relationship("Industry", back_populates="categories")
    template = db.relationship("ProductTemplate", back_populates="categories")
    products = db.relationship("Product", back_populates="category_ref", lazy="dynamic")

    # What this code does: Implements the   repr   logic used by this part of the TracePass application.
    def __repr__(self):
        return f"<ProductCategory {self.name}>"
