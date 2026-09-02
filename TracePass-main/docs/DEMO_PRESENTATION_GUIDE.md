# TracePass Presentation Demo Guide

## Prepare
1. `flask db upgrade`
2. `python seed.py`
3. `python demo_seed.py`
4. Start Flask and open `http://127.0.0.1:5000`

## Demo accounts
Password for demo accounts: `Demo1234!`
- manufacturer@tracepass.demo
- supplier@tracepass.demo
- distributor@tracepass.demo
- retailer@tracepass.demo
- auditor@tracepass.demo

The demo admin remains the admin account configured by `seed.py`.

## End-to-end passport
Passport: `TP-DEMO-2026-001`

The demonstration product contains:
- Manufacturer, supplier, distributor and retailer organizations
- Supplier material offerings
- Organic cotton + recycled polyester composition totaling 100%
- Manufacturing batch
- B2B purchase order and shipment
- Manufacturing, quality, shipment, delivery, receipt and retail events
- Reuse, repair and recycling lifecycle events
- Sustainability/circularity data
- Approved ISO 14001 and OEKO-TEX Standard 100 certificates
- Approved test-report document
- Compliance rule and checks
- Auditor review
- Published passport and QR code

## Recommended live sequence
Landing → Contact Us → Request Account (show authenticity document requirement) → Admin Registration Requests → Approve → Manufacturer → Product Passport → Materials → Supply Chain Timeline → Evidence/Certificates → Compliance → Lifecycle/Sustainability → Publish/QR → Public Passport → Scan/Verify → Verification History.

## QR demonstration
The demo QR is generated to the local host configured by `DEMO_BASE_URL` (default `http://127.0.0.1:5000`). For a LAN presentation, run with a reachable base URL, e.g. `DEMO_BASE_URL=http://192.168.1.20:5000 python demo_seed.py`, then regenerate the QR in that environment.

## Authenticity-document onboarding demo
The included pending request (`applicant@demo-industries.test`) contains two demonstration authenticity documents. Open **Administration → Registration Requests → Review** and show the documents before approving a real request. The approval action is blocked if a request has no authenticity evidence.
