# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
import os
import secrets
import qrcode
from flask import current_app, url_for


# What this code does: Implements the qr static dir logic used by this part of the TracePass application.
def qr_static_dir():
    path = os.path.join(current_app.root_path, "static", "qrcodes")
    os.makedirs(path, exist_ok=True)
    return path


# What this code does: Generates a QR code that links a product passport code to its public TracePass view.
def generate_qr_for_passport_code(passport_code: str) -> str:
    """
    Generates a PNG QR code encoding the public passport verification URL,
    saves it under app/static/qrcodes/<code_value>.png, and returns the
    unique code_value to store on the QRCode model.
    """
    code_value = secrets.token_urlsafe(8)

    # Build the public verification URL the QR will point to.
    # url_for needs a request/app context; caller must be inside one (routes are).
    verify_url = url_for("tracepass.verify_passport", passport_code=passport_code, _external=True)

    img = qrcode.make(verify_url)
    filepath = os.path.join(qr_static_dir(), f"{code_value}.png")
    img.save(filepath)

    return code_value


# What this code does: Implements the qr image url logic used by this part of the TracePass application.
def qr_image_url(code_value: str) -> str:
    return url_for("static", filename=f"qrcodes/{code_value}.png")


# What this code does: Collects and orders product lifecycle events to build a complete traceability timeline.
def build_product_timeline(product):
    """
    Merge supply_chain_events and shipments (via the product's batches) into
    a single chronologically-ordered feed for the traceability timeline view.

    Each entry is a dict with a common shape so the template doesn't need to
    branch on entry type: {kind, timestamp, title, subtitle, detail}.
    """
    entries = []

    for event in product.supply_chain_events.all():
        entries.append({
            "kind": "event",
            "timestamp": event.event_date,
            "title": event.event_type.replace("_", " ").title(),
            "subtitle": event.location or "Location not recorded",
            "detail": event.notes,
            "org": event.organization.name if event.organization else None,
        })

    for batch in product.batches:
        for shipment in batch.shipments:
            # Use shipped_date if present, otherwise fall back to created_at
            # so shipments with only a status update still appear on the timeline.
            ts = shipment.shipped_date or shipment.created_at.date()
            entries.append({
                "kind": "shipment",
                "timestamp": ts,
                "title": f"Shipment {shipment.status.replace('_', ' ').title()}",
                "subtitle": f"Batch {batch.batch_no}",
                "detail": f"Tracking: {shipment.tracking_no}" if shipment.tracking_no else None,
                "org": f"{shipment.from_org.name if shipment.from_org else '?'} → {shipment.to_org.name if shipment.to_org else '?'}",
            })

    # Normalize all timestamps to comparable datetimes for sorting — event_date
    # is a full datetime, shipment dates are plain dates.
    # What this code does: Implements the sort key logic used by this part of the TracePass application.
    def sort_key(e):
        ts = e["timestamp"]
        if hasattr(ts, "hour"):
            return ts
        from datetime import datetime as _dt, time as _time
        return _dt.combine(ts, _time.min)

    entries.sort(key=sort_key)
    return entries
