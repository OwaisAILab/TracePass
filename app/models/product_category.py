# TracePass code note: This module implements the app/models/product_category.py part of the application.
from datetime import datetime, timezone
from app.extensions import db


# Code explanation: Define the Product Category data model or application component used by TracePass.
class ProductCategory(db.Model):
    __tablename__ = "product_categories"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `name` stores this model attribute in the SQL database.
    name = db.Column(db.String(100), nullable=False, unique=True)
    # Database field: `description` stores this model attribute in the SQL database.
    description = db.Column(db.Text, nullable=True)
    # Database field: `industry_id` stores this model attribute in the SQL database.
    industry_id = db.Column(db.Integer, db.ForeignKey("industries.id"), nullable=True, index=True)
    # Database field: `template_id` stores this model attribute in the SQL database.
    template_id = db.Column(db.Integer, db.ForeignKey("product_templates.id"), nullable=True, index=True)
    # Database field: `parent_id` stores this model attribute in the SQL database.
    parent_id = db.Column(db.Integer, db.ForeignKey("product_categories.id"), nullable=True)
    # Database field: `is_active` stores this model attribute in the SQL database.
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    # Database field: `created_at` stores this model attribute in the SQL database.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    parent = db.relationship("ProductCategory", remote_side=[id], backref=db.backref("children", lazy="dynamic"))
    industry = db.relationship("Industry", back_populates="categories")
    template = db.relationship("ProductTemplate", back_populates="categories")
    products = db.relationship("Product", back_populates="category_ref", lazy="dynamic")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<ProductCategory {self.name}>"
