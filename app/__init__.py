import os
from flask import Flask, render_template

from config import config
from app.extensions import db, login_manager, migrate, csrf


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    if config_name == "production":
        config[config_name].validate()

    # --- init extensions ---
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # --- models must be imported before blueprints/migrations touch the DB ---
    from app import models  # noqa: F401

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- automatic audit logging (Phase 5) ---
    from app.reporting.audit import register_audit_listeners
    from app.models.organization import Organization
    from app.models.product import Product, ProductBatch
    from app.models.certificate import Certificate
    from app.models.compliance import ComplianceReview
    from app.models.recall_incident import Recall, Incident
    from app.models.product_category import ProductCategory
    from app.models.lifecycle import LifecycleEvent
    from app.models.registration_request import RegistrationRequest
    from app.models.registration_request_document import RegistrationRequestDocument

    register_audit_listeners([
        User, Organization, Product, ProductBatch, Certificate, ComplianceReview, Recall, Incident, ProductCategory, LifecycleEvent, RegistrationRequest, RegistrationRequestDocument,
    ])

    # --- register blueprints ---
    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp
    from app.main.routes import main_bp
    from app.tracepass.routes import tracepass_bp
    from app.compliance.routes import compliance_bp
    from app.reporting.routes import reporting_bp
    from app.partners.routes import partners_bp
    from app.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(tracepass_bp)
    app.register_blueprint(compliance_bp)
    app.register_blueprint(reporting_bp)
    app.register_blueprint(partners_bp)
    app.register_blueprint(api_bp)

    # --- baseline security headers ---
    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if not app.debug:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

    # --- error handlers ---
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(401)
    def unauthorized(e):
        return render_template("errors/401.html"), 401

    return app
