# TracePass code note: This module implements the app/models/material.py part of the application.
from app.extensions import db


# Code explanation: Define the Material data model or application component used by TracePass.
class Material(db.Model):
    __tablename__ = "materials"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `name` stores this model attribute in the SQL database.
    name = db.Column(db.String(150), nullable=False)
    # Database field: `category` stores this model attribute in the SQL database.
    category = db.Column(db.String(100), nullable=True)
    # Database field: `origin_country` stores this model attribute in the SQL database.
    origin_country = db.Column(db.String(100), nullable=True)
    # Database field: `sustainability_notes` stores this model attribute in the SQL database.
    sustainability_notes = db.Column(db.Text, nullable=True)

    product_links = db.relationship("ProductMaterial", back_populates="material", lazy="dynamic")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<Material {self.name}>"
