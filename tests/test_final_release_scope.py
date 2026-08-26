# TracePass code note: This module implements the tests/test_final_release_scope.py part of the application.
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


# Code explanation: Implement the `test no active ecommerce blueprint or routes` operation used by this part of TracePass.
def test_no_active_ecommerce_blueprint_or_routes():
    source = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "app").rglob("*.py"))
    assert "shop_bp" not in source
    assert "cart_bp" not in source
    assert "checkout" not in source


# Code explanation: Implement the `test single public verify route` operation used by this part of TracePass.
def test_single_public_verify_route():
    source = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "app").rglob("*.py"))
    assert source.count('@tracepass_bp.route("/verify")') == 1
    assert source.count('@tracepass_bp.route("/verify/<passport_code>")') == 1


# Code explanation: Implement the `test final release has security and deployment baseline` operation used by this part of TracePass.
def test_final_release_has_security_and_deployment_baseline():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    uploads = (ROOT / "app" / "uploads.py").read_text(encoding="utf-8")
    api = (ROOT / "app" / "api" / "__init__.py").read_text(encoding="utf-8")
    assert "FLASK_APP=run.py" in dockerfile
    assert "tracepass_uploads:/app/uploads" in compose
    assert "DATABASE_URL=sqlite:///tracepass_dev.db" in env
    assert "ALLOWED_MIME_BY_EXT" in uploads
    assert "validate_upload" in uploads
    assert "csrf.exempt(api_bp)" in api


# Code explanation: Implement the `test general dpp has no store scope in readme` operation used by this part of TracePass.
def test_general_dpp_has_no_store_scope_in_readme():
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    assert "online storefront" in readme
    assert "intentionally removed" in readme
