
from datetime import datetime, timezone
from app.extensions import db

# Defines the product template class and groups its related data and behavior.
class ProductTemplate(db.Model):
    __tablename__ = 'product_templates'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    industry_id = db.Column(db.Integer, db.ForeignKey('industries.id'), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    industry = db.relationship('Industry', back_populates='templates')
    fields = db.relationship('TemplateField', back_populates='template', cascade='all, delete-orphan', order_by='TemplateField.sort_order')
    categories = db.relationship('ProductCategory', back_populates='template')
# Provides the internal repr helper used by this module's workflow.
    def __repr__(self): return f'<ProductTemplate {self.name}>'

# Defines the template field class and groups its related data and behavior.
class TemplateField(db.Model):
    __tablename__ = 'template_fields'
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('product_templates.id'), nullable=False)
    key = db.Column(db.String(80), nullable=False)
    label = db.Column(db.String(150), nullable=False)
    field_type = db.Column(db.String(20), nullable=False, default='text')
    required = db.Column(db.Boolean, nullable=False, default=False)
    help_text = db.Column(db.String(255), nullable=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    template = db.relationship('ProductTemplate', back_populates='fields')
    __table_args__ = (db.UniqueConstraint('template_id', 'key', name='uq_template_field_key'),)
# Provides the internal repr helper used by this module's workflow.
    def __repr__(self): return f'<TemplateField {self.key}>'
