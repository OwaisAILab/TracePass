# TracePass code note: This module implements the app/models/product.py part of the application.
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


# Code explanation: Implement the `generate passport code` operation used by this part of TracePass.
def generate_passport_code() -> str:
    # Short, URL-safe, unique-enough identifier. Collision handled by
    # unique constraint + retry in the create-product route, not here.
    return "TP-" + secrets.token_hex(4).upper()


# Code explanation: Define the Product data model or application component used by TracePass.
class Product(db.Model):
    __tablename__ = "products"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `passport_code` stores this model attribute in the SQL database.
    passport_code = db.Column(db.String(50), unique=True, nullable=False, default=generate_passport_code)
    # Database field: `name` stores this model attribute in the SQL database.
    name = db.Column(db.String(150), nullable=False)
    # Legacy display field retained for backward compatibility with existing rows.
    # Database field: `category` stores this model attribute in the SQL database.
    category = db.Column(db.String(100), nullable=True)
    # Database field: `category_id` stores this model attribute in the SQL database.
    category_id = db.Column(db.Integer, db.ForeignKey("product_categories.id"), nullable=True, index=True)
    # Database field: `brand` stores this model attribute in the SQL database.
    brand = db.Column(db.String(100), nullable=True)
    # Database field: `model` stores this model attribute in the SQL database.
    model = db.Column(db.String(100), nullable=True)
    # Database field: `description` stores this model attribute in the SQL database.
    description = db.Column(db.Text, nullable=True)
    # Database field: `manufacturer_org_id` stores this model attribute in the SQL database.
    manufacturer_org_id = db.Column(db.Integer, db.ForeignKey("organizations.id"), nullable=False)
    # Database field: `status` stores this model attribute in the SQL database.
    status = db.Column(db.String(20), default=STATUS_DRAFT, nullable=False)
    # Database field: `compliance_status` stores this model attribute in the SQL database.
    compliance_status = db.Column(db.String(20), default=COMPLIANCE_PENDING, nullable=False)
    # Database field: `image_url` stores this model attribute in the SQL database.
    image_url = db.Column(db.String(500), nullable=True)  # optional public passport product image
    # Database field: `attribute_values` stores this model attribute in the SQL database.
    attribute_values = db.Column(db.Text, nullable=True)  # JSON values defined by the category template
    # Database field: `sustainability_data` stores this model attribute in the SQL database.
    sustainability_data = db.Column(db.Text, nullable=True)  # JSON/text sustainability and circularity disclosures
    # Database field: `created_at` stores this model attribute in the SQL database.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    manufacturer = db.relationship("Organization")
    category_ref = db.relationship("ProductCategory", back_populates="products")
    batches = db.relationship("ProductBatch", back_populates="product", cascade="all, delete-orphan")
    materials = db.relationship("ProductMaterial", back_populates="product", cascade="all, delete-orphan")
    qr_code = db.relationship("QRCode", back_populates="product", uselist=False, cascade="all, delete-orphan")

    # --- publish readiness check (spec section 6: mandatory fields before publish) ---
    # Code explanation: Implement the `get attribute values` operation used by this part of TracePass.
    def get_attribute_values(self):
        try:
            return json.loads(self.attribute_values or "{}")
        except (TypeError, ValueError):
            return {}

    # Code explanation: Implement the `material percentage total` operation used by this part of TracePass.
    def material_percentage_total(self):
        """Return the sum of declared material percentages.

        A passport may contain quantity-only material links, so percentages
        that are not supplied are ignored.
        """
        return round(sum((link.percentage or 0) for link in self.materials), 2)

    # Code explanation: Implement the `missing required fields` operation used by this part of TracePass.
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

    # Code explanation: Implement the `can publish` operation used by this part of TracePass.
    def can_publish(self) -> bool:
        return len(self.missing_required_fields()) == 0

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<Product {self.passport_code}>"


# Code explanation: Define the Product Batch data model or application component used by TracePass.
class ProductBatch(db.Model):
    __tablename__ = "product_batches"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `product_id` stores this model attribute in the SQL database.
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    # Database field: `batch_no` stores this model attribute in the SQL database.
    batch_no = db.Column(db.String(100), nullable=False)
    # Database field: `manufacture_date` stores this model attribute in the SQL database.
    manufacture_date = db.Column(db.Date, nullable=True)
    # Database field: `production_location` stores this model attribute in the SQL database.
    production_location = db.Column(db.String(150), nullable=True)
    # Database field: `quantity` stores this model attribute in the SQL database.
    quantity = db.Column(db.Integer, nullable=True)

    product = db.relationship("Product", back_populates="batches")
    events = db.relationship("SupplyChainEvent", back_populates="batch", lazy="dynamic")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<ProductBatch {self.batch_no}>"


# Code explanation: Define the Product Material data model or application component used by TracePass.
class ProductMaterial(db.Model):
    __tablename__ = "product_materials"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `product_id` stores this model attribute in the SQL database.
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    # Database field: `material_id` stores this model attribute in the SQL database.
    material_id = db.Column(db.Integer, db.ForeignKey("materials.id"), nullable=False)
    # Database field: `supplier_id` stores this model attribute in the SQL database.
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=True)
    # Database field: `quantity` stores this model attribute in the SQL database.
    quantity = db.Column(db.Float, nullable=True)
    # Database field: `percentage` stores this model attribute in the SQL database.
    percentage = db.Column(db.Float, nullable=True)

    product = db.relationship("Product", back_populates="materials")
    material = db.relationship("Material", back_populates="product_links")
    supplier = db.relationship("Supplier", back_populates="material_links")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<ProductMaterial product={self.product_id} material={self.material_id}>"


# Code explanation: Define the Q R Code data model or application component used by TracePass.
class QRCode(db.Model):
    __tablename__ = "qr_codes"

    # Database field: `id` stores this model attribute in the SQL database.
    id = db.Column(db.Integer, primary_key=True)
    # Database field: `product_id` stores this model attribute in the SQL database.
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), unique=True, nullable=False)
    # Database field: `code_value` stores this model attribute in the SQL database.
    code_value = db.Column(db.String(100), unique=True, nullable=False)
    # Database field: `generated_at` stores this model attribute in the SQL database.
    generated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    product = db.relationship("Product", back_populates="qr_code")

    # Code explanation: Python special method `__repr__` used by the class or framework.
    def __repr__(self):
        return f"<QRCode {self.code_value}>"
