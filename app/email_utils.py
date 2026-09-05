
import logging
import secrets
import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app
from app.extensions import db
from app.models.email_otp import (
    EmailOTP,
    OTP_PURPOSE_CUSTOMER_REGISTRATION,
    OTP_PURPOSE_ORG_REQUEST,
)

logger = logging.getLogger(__name__)


#  Generates otp code from the available project data.
def generate_otp_code(length: int = 6) -> str:
    """Generate a cryptographically secure numeric OTP code."""
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))


# Implements the build otp email content operation used by this module.
def build_otp_email_content(otp_code: str, purpose: str, recipient_name: str = None) -> tuple[str, str, str]:
    """Generate subject, HTML body, and plain text body for the OTP email."""
    name_greeting = f"Hello {recipient_name}," if recipient_name else "Hello,"
    expiry_min = current_app.config.get("OTP_EXPIRY_MINUTES", 10)

    if purpose == OTP_PURPOSE_CUSTOMER_REGISTRATION:
        action_desc = "complete your TracePass customer account registration"
        context_note = "Once verified, your account will be activated immediately and you can begin verifying product passports."
    else:
        action_desc = "validate your email address for your TracePass organizational account request"
        context_note = "Once verified, your request will be automatically forwarded to our administrative team for verification and review."

    subject = f"Your TracePass Verification Code: {otp_code}"

    text_body = f"""{name_greeting}

Your One-Time Password (OTP) to {action_desc} is:

{otp_code}

This code is valid for {expiry_min} minutes. Please do not share this code with anyone.

{context_note}

If you did not request this verification code, please ignore this email.

Best regards,
TracePass Security Team
https://tracepass.app
"""

    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TracePass Verification Code</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: #f8fafc;
      color: #1e293b;
      margin: 0;
      padding: 0;
    }}
    .email-wrapper {{
      max-width: 580px;
      margin: 30px auto;
      background: #ffffff;
      border-radius: 12px;
      overflow: hidden;
      border: 1px solid #e2e8f0;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }}
    .email-header {{
      background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
      padding: 30px 40px;
      text-align: center;
      color: #ffffff;
    }}
    .email-header h1 {{
      margin: 0;
      font-size: 24px;
      letter-spacing: -0.5px;
      font-weight: 700;
    }}
    .email-header p {{
      margin: 6px 0 0;
      font-size: 13px;
      color: #93c5fd;
      text-transform: uppercase;
      letter-spacing: 1px;
      font-weight: 600;
    }}
    .email-body {{
      padding: 36px 40px;
    }}
    .otp-box {{
      background: #f1f5f9;
      border: 2px dashed #cbd5e1;
      border-radius: 10px;
      padding: 20px;
      text-align: center;
      margin: 28px 0;
    }}
    .otp-code {{
      font-family: 'Courier New', Courier, monospace;
      font-size: 36px;
      font-weight: 800;
      color: #1e3a8a;
      letter-spacing: 8px;
      margin: 0;
    }}
    .otp-expiry {{
      font-size: 12px;
      color: #64748b;
      margin-top: 8px;
    }}
    .email-footer {{
      border-top: 1px solid #e2e8f0;
      padding: 20px 40px;
      text-align: center;
      font-size: 12px;
      color: #94a3b8;
      background-color: #fafbfc;
    }}
  </style>
</head>
<body>
  <div class="email-wrapper">
    <div class="email-header">
      <h1>TracePass</h1>
      <p>Digital Product Passport Platform</p>
    </div>
    <div class="email-body">
      <p style="font-size: 16px; font-weight: 600; margin-top: 0;">{name_greeting}</p>
      <p style="color: #475569; line-height: 1.6; font-size: 14px;">
        Please use the following One-Time Password (OTP) to {action_desc}:
      </p>
      <div class="otp-box">
        <div class="otp-code">{otp_code}</div>
        <div class="otp-expiry">Valid for {expiry_min} minutes &bull; Single-use code</div>
      </div>
      <p style="color: #475569; line-height: 1.6; font-size: 14px;">
        {context_note}
      </p>
      <p style="color: #64748b; font-size: 12px; line-height: 1.5; margin-top: 24px; padding-top: 16px; border-top: 1px solid #f1f5f9;">
        <strong>Security Notice:</strong> If you did not initiate this request, please disregard this email. TracePass will never ask you for your verification code.
      </p>
    </div>
    <div class="email-footer">
      &copy; {datetime.now(timezone.utc).year} TracePass Platform. All rights reserved.
    </div>
  </div>
</body>
</html>
"""
    return subject, html_body, text_body


#  Sends email using the configured notification or email service.
def send_email(to_email: str, subject: str, html_body: str, text_body: str) -> bool:
    """Send an email using configured SMTP parameters, with graceful fallback logging."""
    mail_server = current_app.config.get("MAIL_SERVER")
    mail_port = current_app.config.get("MAIL_PORT", 587)
    mail_use_tls = current_app.config.get("MAIL_USE_TLS", True)
    mail_use_ssl = current_app.config.get("MAIL_USE_SSL", False)
    mail_username = current_app.config.get("MAIL_USERNAME")
    mail_password = current_app.config.get("MAIL_PASSWORD")
    mail_sender = current_app.config.get("MAIL_DEFAULT_SENDER", "noreply@tracepass.com")

    # If SMTP is not fully configured, log the email clearly (essential for local dev & testing)
    if not mail_username or not mail_password or current_app.config.get("TESTING"):
        current_app.logger.info(
            f"[EMAIL SERVICE - DEV/MOCK] Sent to: {to_email} | Subject: {subject}"
        )
        print(f"\n==================== [DEV EMAIL / OTP] ====================")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Content:\n{text_body}")
        print(f"===========================================================\n")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = mail_sender
        msg["To"] = to_email

        part1 = MIMEText(text_body, "plain", "utf-8")
        part2 = MIMEText(html_body, "html", "utf-8")
        msg.attach(part1)
        msg.attach(part2)

        if mail_use_ssl:
            server = smtplib.SMTP_SSL(mail_server, mail_port, timeout=10)
        else:
            server = smtplib.SMTP(mail_server, mail_port, timeout=10)
            if mail_use_tls:
                server.starttls()

        server.login(mail_username, mail_password)
        server.sendmail(mail_sender, [to_email], msg.as_string())
        server.quit()
        current_app.logger.info(f"Email successfully delivered to {to_email}")
        return True
    except Exception as e:
        current_app.logger.warning(
            f"Failed to send email via SMTP to {to_email}: {e}. Fallback logged."
        )
        print(f"\n[SMTP Warning - Email Delivery Fallback] To: {to_email} | Error: {e}")
        print(f"OTP Subject: {subject}\n{text_body}\n")
        return False


# Implements the create and send otp operation used by this module.
def create_and_send_otp(
    email: str,
    purpose: str,
    payload: str = None,
    request_id: int = None,
    recipient_name: str = None,
) -> tuple[EmailOTP, bool]:
    """Create a new OTP record in the DB, superseding prior active ones, and dispatch the email."""
    email_clean = email.lower().strip()

    # Invalidate previous unused OTPs for this email and purpose
    old_otps = EmailOTP.query.filter_by(
        email=email_clean, purpose=purpose, is_used=False
    ).all()
    for old in old_otps:
        old.is_used = True

    otp_code = generate_otp_code(6)
    expiry_minutes = current_app.config.get("OTP_EXPIRY_MINUTES", 10)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)

    otp_record = EmailOTP(
        email=email_clean,
        otp_code=otp_code,
        purpose=purpose,
        payload=payload,
        request_id=request_id,
        expires_at=expires_at,
        is_used=False,
        attempts=0,
    )
    db.session.add(otp_record)
    db.session.commit()

    subject, html_body, text_body = build_otp_email_content(
        otp_code=otp_code, purpose=purpose, recipient_name=recipient_name
    )
    sent_success = send_email(email_clean, subject, html_body, text_body)

    return otp_record, sent_success


# Implements the verify otp code operation used by this module.
def verify_otp_code(email: str, purpose: str, code: str) -> tuple[bool, str, EmailOTP | None]:
    """
    Validate a user-submitted OTP code.
    Returns (is_valid, message, otp_record).
    """
    email_clean = email.lower().strip()
    code_clean = (code or "").strip()

    if not code_clean or len(code_clean) != 6 or not code_clean.isdigit():
        return False, "Please enter a valid 6-digit verification code.", None

    otp_record = (
        EmailOTP.query.filter_by(email=email_clean, purpose=purpose, is_used=False)
        .order_by(EmailOTP.created_at.desc())
        .first()
    )

    if not otp_record:
        return False, "No active verification code found for this email. Please request a new code.", None

    if otp_record.is_expired:
        otp_record.is_used = True
        db.session.commit()
        return False, "Your verification code has expired. Please request a new code.", None

    if otp_record.attempts >= 5:
        otp_record.is_used = True
        db.session.commit()
        return False, "Maximum verification attempts exceeded. Please request a new code.", None

    if otp_record.otp_code != code_clean:
        otp_record.attempts += 1
        db.session.commit()
        remaining = 5 - otp_record.attempts
        return False, f"Incorrect verification code. {remaining} attempt{'s' if remaining != 1 else ''} remaining.", None

    # Valid OTP
    otp_record.is_used = True
    db.session.commit()
    return True, "Verification successful.", otp_record
