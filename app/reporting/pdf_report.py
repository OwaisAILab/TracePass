# TracePass code note: This module implements the app/reporting/pdf_report.py part of the application.
import os
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch


# Code explanation: Implement the `build compliance report pdf` operation used by this part of TracePass.
def build_compliance_report_pdf(product, certificates, checks, reviews, output_path):
    """Builds a compliance report PDF for a single product and writes it to output_path."""
    doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("TracePass Compliance Report", styles["Title"]))
    story.append(Paragraph(f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
    story.append(Spacer(1, 16))

    story.append(Paragraph(f"{product.name} ({product.passport_code})", styles["Heading1"]))
    identity_rows = [
        ["Category", product.category or "—"],
        ["Brand", product.brand or "—"],
        ["Manufacturer", product.manufacturer.name if product.manufacturer else "—"],
        ["Status", product.status],
        ["Compliance Status", product.compliance_status],
    ]
    identity_table = Table(identity_rows, colWidths=[150, 350])
    identity_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(identity_table)
    story.append(Spacer(1, 16))

    story.append(Paragraph("Certificates", styles["Heading2"]))
    if certificates:
        cert_rows = [["Type", "Number", "Expiry", "Status"]]
        for c in certificates:
            status = "Expired" if c.is_expired() else ("Expiring Soon" if c.expires_soon() else "Valid")
            cert_rows.append([c.cert_type, c.cert_number or "—", str(c.expiry_date or "—"), status])
        cert_table = Table(cert_rows, colWidths=[130, 110, 100, 100])
        cert_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ]))
        story.append(cert_table)
    else:
        story.append(Paragraph("No certificates on file.", styles["Normal"]))
    story.append(Spacer(1, 16))

    story.append(Paragraph("Compliance Check History", styles["Heading2"]))
    if checks:
        check_rows = [["Result", "Requirement", "Reason", "Checked At"]]
        for c in checks:
            check_rows.append([
                c.result.upper(),
                c.requirement.required_value,
                Paragraph(c.reason or "—", styles["Normal"]),
                c.checked_at.strftime("%Y-%m-%d %H:%M"),
            ])
        check_table = Table(check_rows, colWidths=[50, 100, 220, 90])
        check_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(check_table)
    else:
        story.append(Paragraph("No compliance checks have been run.", styles["Normal"]))
    story.append(Spacer(1, 16))

    story.append(Paragraph("Officer Reviews", styles["Heading2"]))
    if reviews:
        review_rows = [["Decision", "Reviewer", "Date", "Reasoning"]]
        for r in reviews:
            review_rows.append([
                r.decision.replace("_", " ").title(),
                r.reviewer.name,
                r.reviewed_at.strftime("%Y-%m-%d"),
                Paragraph(r.reasoning or "—", styles["Normal"]),
            ])
        review_table = Table(review_rows, colWidths=[90, 100, 70, 200])
        review_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(review_table)
    else:
        story.append(Paragraph("No officer reviews recorded.", styles["Normal"]))

    doc.build(story)
    return output_path
