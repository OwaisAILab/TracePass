# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
import secrets
import json
from datetime import datetime, timezone
from app.extensions import db

STATUS_DRAFT = "draft"
STATUS_SUBMITTED = "submitted"
STATUS_PUBLISHED = "published"
STATUS_ARCHIVED = "archived"
PRODUCT_STATUSES = [STATUS_DRAFT, STATUS_SUBMITTED, STATUS_PUBLISHED, STATUS_ARCHIVED]

COMPLIANCE_PENDING = "pending"
COMPLIANCE_COMPLIANT = "compliant"
COMPLIANCE_NON_COMPLIANT = "non_compliant"
COMPLIANCE_STATUSES = [COMPLIANCE_PENDING, COMPLIANCE_COMPLIANT, COMPLIANCE_NON_COMPLIANT]


# What this code does: Generates passport code from the available project data.
def generate_passport_code() -> str:
    # Short, URL-safe, unique-enough identifier. Collision handled by
    # unique constraint + retry in the create-product route, not here.
    return "TP-" + secrets.token_hex(4).upper()


# What this code does: Defines the Product class, grouping related data and behavior used by this part of the application.
class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    passport_code = db.Column(db.String(50), unique=True, nullable=False, default=generate_passport_code)
    name = db.Column(db.String(150), nullable=False)
    # Legacy display field retained for backward compatibility with existing rows.
    category = db.Column(db.String(100), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey("product_categories.id"), nullable=True, index=True)
    brand = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    manufacturer_org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    status = db.Column(db.String(20), default=STATUS_DRAFT, nullable=False)
    compliance_status = db.Column(db.String(20), default=COMPLIANCE_PENDING, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)  # optional public passport product image
    attribute_values = db.Column(db.Text, nullable=True)  # JSON values defined by the category template
    sustainability_data = db.Column(db.Text, nullable=True)  # JSON/text sustainability and circularity disclosures
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    manufacturer = db.relationship("Organization")
    category_ref = db.relationship("ProductCategory", back_populates="products")
    batches = db.relationship("ProductBatch", back_populates="product", cascade="all, delete-orphan")
    materials = db.relationship("ProductMaterial", back_populates="product", cascade="all, delete-orphan")
    qr_code = db.relationship("QRCode", back_populates="product", uselist=False, cascade="all, delete-orphan")

    # --- publish readiness check (spec section 6: mandatory fields before publish) ---
    # What this code does: Retrieves attribute values needed by the surrounding feature.
    def get_attribute_values(self):
        try:
            return json.loads(self.attribute_values or "{}")
        except (TypeError, ValueError):
            return {}

    # What this code does: Implements the material percentage total logic used by this part of the TracePass application.
    def material_percentage_total(self):
        """Return the sum of declared material percentages.

        A passport may contain quantity-only material links, so percentages
        that are not supplied are ignored.
        """
        return round(sum((link.percentage or 0) for link in self.materials), 2)

    # What this code does: Implements the missing required fields logic used by this part of the TracePass application.
    def missing_required_fields(self):
        missing = []
        if not self.name:
            missing.append("name")
        if not self.category_id and not self.category:
            missing.append("product category")
        if not self.manufacturer_org_id:
            missing.append("manufacturer")
        if not self.batches:
            missing.append("at least one manufacturing batch")
        category = self.category_ref
        if category and category.template and category.template.is_active:
            values = self.get_attribute_values()
            for field in category.template.fields:
                if field.required and not str(values.get(field.key, "")).strip():
                    missing.append(field.label)
        if not self.materials:
            missing.append("at least one material")
        elif any(link.percentage is not None for link in self.materials):
            total = self.material_percentage_total()
            if abs(total - 100) > 0.01:
                missing.append(f"material composition totaling 100% (currently {total:g}%)")
        return missing

    # What this code does: Determines whether the current object or user is allowed to perform the requested action.
    def can_publish(self) -> bool:
        return len(self.missing_required_fields()) == 0

    # What this code does: Implements the   repr   logic used by this part of the TracePass application.
    def __repr__(self):
        return f"<Product {self.passport_code}>"


# What this code does: Defines the ProductBatch class, grouping related data and behavior used by this part of the application.
class ProductBatch(db.Model):
    __tablename__ = "product_batches"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    batch_no = db.Column(db.String(100), nullable=False)
    manufacture_date = db.Column(db.Date, nullable=True)
    production_location = db.Column(db.String(150), nullable=True)
    quantity = db.Column(db.Integer, nullable=True)

    product = db.relationship("Product", back_populates="batches")
    events = db.relationship("SupplyChainEvent", back_populates="batch", lazy="dynamic")

    # What this code does: Implements the   repr   logic used by this part of the TracePass application.
    def __repr__(self):
        return f"<ProductBatch {self.batch_no}>"


# What this code does: Defines the ProductMaterial class, grouping related data and behavior used by this part of the application.
class ProductMaterial(db.Model):
    __tablename__ = "product_materials"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey("materials.id"), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=True)
    quantity = db.Column(db.Float, nullable=True)
    percentage = db.Column(db.Float, nullable=True)

    product = db.relationship("Product", back_populates="materials")
    material = db.relationship("Material", back_populates="product_links")
    supplier = db.relationship("Supplier", back_populates="material_links")

    # What this code does: Implements the   repr   logic used by this part of the TracePass application.
    def __repr__(self):
        return f"<ProductMaterial product={self.product_id} material={self.material_id}>"


# What this code does: Defines the QRCode class, grouping related data and behavior used by this part of the application.
class QRCode(db.Model):
    __tablename__ = "qr_codes"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), unique=True, nullable=False)
    code_value = db.Column(db.String(100), unique=True, nullable=False)
    generated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    product = db.relationship("Product", back_populates="qr_code")

    # What this code does: Implements the   repr   logic used by this part of the TracePass application.
    def __repr__(self):
        return f"<QRCode {self.code_value}>"
