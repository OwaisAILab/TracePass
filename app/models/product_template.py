# TracePass code note: This module implements the app/models/product_template.py part of the application.
from datetime import datetime, timezone
from app.extensions import db

# Code explanation: Define the Product Template data model or application component used by TracePass.
class ProductTemplate(db.Model):
    __tablename__ = 'product_templates'
    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `name` stores this model attribute in the SQL database.
    name = db.Column(db.String(150), nullable=False)
    # Database field: `description` stores this model attribute in the SQL database.
    description = db.Column(db.Text, nullable=True)
    # Database field: `industry_id` stores this model attribute in the SQL database.
    industry_id = db.Column(db.Integer, db.ForeignKey('industries.id'), nullable=False)
    # Database field: `is_active` stores this model attribute in the SQL database.
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    # Database field: `created_at` stores this model attribute in the SQL database.
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    industry = db.relationship('Industry', back_populates='templates')
    fields = db.relationship('TemplateField', back_populates='template', cascade='all, delete-orphan', order_by='TemplateField.sort_order')
    categories = db.relationship('ProductCategory', back_populates='template')
    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self): return f'<ProductTemplate {self.name}>'

# Code explanation: Define the Template Field data model or application component used by TracePass.
class TemplateField(db.Model):
    __tablename__ = 'template_fields'
    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `template_id` stores this model attribute in the SQL database.
    template_id = db.Column(db.Integer, db.ForeignKey('product_templates.id'), nullable=False)
    # Database field: `key` stores this model attribute in the SQL database.
    key = db.Column(db.String(80), nullable=False)
    # Database field: `label` stores this model attribute in the SQL database.
    label = db.Column(db.String(150), nullable=False)
    # Database field: `field_type` stores this model attribute in the SQL database.
    field_type = db.Column(db.String(20), nullable=False, default='text')
    # Database field: `required` stores this model attribute in the SQL database.
    required = db.Column(db.Boolean, nullable=False, default=False)
    # Database field: `help_text` stores this model attribute in the SQL database.
    help_text = db.Column(db.String(255), nullable=True)
    # Database field: `sort_order` stores this model attribute in the SQL database.
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    template = db.relationship('ProductTemplate', back_populates='fields')
    __table_args__ = (db.UniqueConstraint('template_id', 'key', name='uq_template_field_key'),)
    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self): return f'<TemplateField {self.key}>'
