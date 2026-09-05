
from app.models.role import Role  # noqa: F401
from app.models.organization import Organization  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.material import Material  # noqa: F401
from app.models.supplier import Supplier  # noqa: F401
from app.models.supplier_material import SupplierMaterial  # noqa: F401
from app.models.product import Product, ProductBatch, ProductMaterial, QRCode  # noqa: F401
from app.models.supply_chain_event import SupplyChainEvent  # noqa: F401
from app.models.shipment import Shipment  # noqa: F401
from app.models.certificate import Certificate, Document  # noqa: F401
from app.models.compliance import (  # noqa: F401
    ComplianceRule,
    ComplianceRequirement,
    ComplianceCheck,
    ComplianceReview,
)
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.recall_incident import Recall, Incident  # noqa: F401
from app.models.purchase_order import PurchaseOrder  # noqa: F401

# Phase 6 adds REST API resources on top of these models — no new tables expected.
from app.models.product_category import ProductCategory  # noqa: F401

from app.models.purchase_order_offer import PurchaseOrderOffer

from app.models.industry import Industry  # noqa: F401
from app.models.product_template import ProductTemplate, TemplateField  # noqa: F401

from app.models.lifecycle import LifecycleEvent  # noqa: F401
from app.models.verification import VerificationLog  # noqa: F401
from app.models.registration_request import RegistrationRequest  # noqa: F401

from app.models.registration_request_document import RegistrationRequestDocument  # noqa: F401

from app.models.email_verification import EmailVerification  # noqa: F401
