# TracePass code note: This module implements the app/models/industry.py part of the application.
from datetime import datetime, timezone
from app.extensions import db

# Code explanation: Define the Industry data model or application component used by TracePass.
class Industry(db.Model):
    __tablename__ = 'industries'
    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `name` stores this model attribute in the SQL database.
    name = db.Column(db.String(120), nullable=False, unique=True)
    # Database field: `description` stores this model attribute in the SQL database.
    description = db.Column(db.Text, nullable=True)
    # Database field: `image_url` stores this model attribute in the SQL database.
    image_url = db.Column(db.String(255), nullable=True)
    # Database field: `is_active` stores this model attribute in the SQL database.
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    # Database field: `created_at` stores this model attribute in the SQL database.
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    categories = db.relationship('ProductCategory', back_populates='industry')
    templates = db.relationship('ProductTemplate', back_populates='industry')
    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self): return f'<Industry {self.name}>'
