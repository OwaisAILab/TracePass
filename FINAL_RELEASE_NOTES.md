# TracePass Final Release

## Scope
This release is the general-purpose Digital Product Passport platform. The online storefront, shopping cart, checkout, customer e-commerce orders, and shop blueprint have been removed completely from the application code.

B2B procurement purchase orders remain because they are supply-chain transactions, not consumer e-commerce.

## Final hardening included

- Single canonical public QR verification route: `/verify` and `/verify/<passport_code>`.
- Compliance rules use the authoritative `ProductCategory` foreign key.
- Legacy rule category names are migrated to category IDs where a matching category exists.
- Certificate evidence now has an explicit pending/approved/rejected review lifecycle.
- Approved certificate evidence is required by the compliance engine.
- Certificate review automatically re-runs compliance for the affected product(s).
- Category-template required fields are enforced by the publish readiness check.
- Server-side file validation checks extension, MIME and basic file signatures.
- Product images are uploaded from the local computer and validated as real images.
- Password registration/admin creation requires upper/lowercase characters and a number.
- REST API blueprint is exempt from browser CSRF while browser forms retain CSRF protection.
- Public passport verification attempts are recorded as append-only verification history (verified/unpublished/invalid).
- Lifecycle events are recorded and surfaced in internal and public passport views.
- Sustainability/circularity disclosure is supported on the passport and public API.
- Internal product API endpoints require authentication; public access is limited to published public-passport data.
- Docker declares `FLASK_APP` and persists `/app/uploads` using a named volume.
- `.env.example` provides a working SQLite development default.
- Distributor/Retailer operations have a dedicated receiving/outbound operations view.
- Store-only product price field is removed from the model and database through the final migration.
- Legacy cart/order tables are removed by the final migration if they exist.

## Recommended first run

1. Create and activate a Python 3.11 virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and change the secret/admin password for real use.
4. Run `flask db upgrade`.
5. Run `python seed.py` if seed data is required.
6. Run `flask run`.

For an existing TracePass database, **do not delete the database**. Run `flask db upgrade`; the final migration removes obsolete store/cart tables and normalizes the compliance schema.

## Demonstration story

Admin → Industry/Category/Template → Compliance Rule → Manufacturer creates passport → batch/materials → certificate upload → Auditor reviews evidence → compliance automatically re-runs → manufacturer publishes → QR generated → Distributor/Retailer receives/transfers → public user scans QR → Digital Product Passport is displayed.
