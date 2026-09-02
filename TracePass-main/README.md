# TracePass

Flask-based digital product passport and supply-chain compliance system.

**Status:** Phases 1–5 complete; Phase 6 professional deployment baseline implemented.

## Setup

### 1. Create and activate a virtual environment

Always use a venv for this project — it keeps TracePass's dependencies isolated
from your system Python and from other projects.

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

Your terminal prompt should show `(venv)` once it's active. Every command
below assumes the venv is active — if you close your terminal, reactivate it
before running anything.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up the database

**First run is required before login.** A fresh ZIP does not contain a populated SQLite database. On Windows you can run `setup_windows.bat`, or run:

```bash
flask db upgrade
python seed.py
```

This creates `tracepass_dev.db` (SQLite), seeds the 6 roles, and creates a
default admin account:

- **Email:** `admin@tracepass.example`
- **Password:** `ChangeMe123!`

Change this password immediately if you deploy this anywhere beyond local dev.

### 4. Run the app

```bash
flask run
```

Visit `http://127.0.0.1:5000`.

## Project structure

```
app/
├── auth/          # login, registration, logout
├── admin/         # user & organization management (admin only)
├── main/          # dashboard landing page
├── tracepass/     # product passports, batches, materials, QR codes
├── models/        # SQLAlchemy models
├── templates/      # Jinja2 templates
└── static/        # CSS, generated QR code images
config.py          # dev/test/prod configuration
seed.py            # database seeding script
run.py             # app entry point
migrations/        # Flask-Migrate/Alembic migration history
```

## Running tests

```bash
pytest -q
```

`tests/test_api.py` covers the REST API. `tests/test_core_requirements.py` covers
the rest of spec section 27's testing expectations: authentication and role
permissions, invalid-input validation, compliance-engine business rules, file
upload restrictions, and a full create → publish → public-verify workflow.

## When you're done working

Deactivate the virtual environment:
```bash
deactivate
```

## Phase 5 — Reporting & Controls

Phase 5 adds the control layer required by the TracePass specification:
- Role-aware reporting dashboard and compliance KPIs
- Notification center with unread/read handling
- Certificate expiry, failed-check, pending-review and recall alerts
- Recall and incident lifecycle management
- Automatic append-only audit logging for critical records
- Search/filter/pagination for administrator audit logs
- CSV export of reporting KPIs
- Existing per-product compliance PDF reports
- Public passport/QR verification remains available from published products
- Certificate/document evidence is downloadable (not just uploadable) by admin, manufacturer and auditor roles

### Phase 6 — Professional Deployment

Phase 6 adds the professional deployment baseline required by the TracePass specification:
- REST API under `/api/v1` with health, product, public passport and reporting endpoints
- Automated pytest coverage for API and access-control basics
- PostgreSQL production configuration through `DATABASE_URL`
- Dockerfile and Docker Compose with PostgreSQL
- Environment-variable template and production security checklist

See `docs/PHASE6.md` for API and deployment details.

### Phase 5 test flow
1. Login as Admin and open Dashboard.
2. Confirm KPI cards and Notification Center.
3. Create/modify a product, certificate or compliance review and confirm an audit entry.
4. Issue a recall from a product passport and confirm it appears on the dashboard.
5. Report an incident and update it to Investigating/Resolved.
6. Trigger a failed compliance check and confirm the appropriate role receives an alert.
7. Open Notification Center, dismiss an alert and use Mark all as read.
8. Open Audit Log, filter by action/entity/search term.
9. Export the reporting summary CSV.
10. Open the public passport through the QR/public verification link.

## Final Release Scope

TracePass is a general Digital Product Passport platform. The online storefront, shopping cart, checkout and customer e-commerce order modules are intentionally removed from this release. Procurement purchase orders between supply-chain organizations remain because they are part of traceability and sourcing workflows.

Core verification flow: product → evidence → review → compliance → publish → QR scan → public passport.

## Presentation demo dataset

For a presentation-ready environment, after `flask db upgrade` and `python seed.py`, run:

```text
python demo_seed.py
```

This creates a multi-organization demonstration flow with manufacturer, supplier, distributor, retailer and auditor users, a published passport (`TP-DEMO2026`), batch/material traceability, shipment, lifecycle events, sustainability disclosure, QR verification and verification history.

Demo password for the demo accounts: `Demo1234!`

- Admin: `admin@tracepass.demo`
- Manufacturer: `manufacturer@tracepass.demo`
- Supplier: `supplier@tracepass.demo`
- Distributor: `distributor@tracepass.demo`
- Retailer: `retailer@tracepass.demo`
- Auditor: `auditor@tracepass.demo`
