
from datetime import datetime, timezone
from app.extensions import db

# Defines the industry class and groups its related data and behavior.
class Industry(db.Model):
    __tablename__ = 'industries'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    categories = db.relationship('ProductCategory', back_populates='industry')
    templates = db.relationship('ProductTemplate', back_populates='industry')
# Provides the internal repr helper used by this module's workflow.
    def __repr__(self): return f'<Industry {self.name}>'
