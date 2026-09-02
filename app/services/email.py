import smtplib
from email.message import EmailMessage

from flask import current_app


def send_email(to_address: str, subject: str, text_body: str, html_body: str | None = None) -> None:
    """Send an email using the SMTP settings configured in the environment.

    TracePass intentionally uses the standard library here, avoiding another
    mail dependency. In production, configure MAIL_SERVER/PORT/USERNAME/PASSWORD.
    """
    server_name = current_app.config.get("MAIL_SERVER")
    username = current_app.config.get("MAIL_USERNAME")
    password = current_app.config.get("MAIL_PASSWORD")
    sender = current_app.config.get("MAIL_DEFAULT_SENDER") or username

    if not server_name or not sender:
        raise RuntimeError(
            "Email service is not configured. Set MAIL_SERVER and MAIL_DEFAULT_SENDER "
            "(plus MAIL_USERNAME/MAIL_PASSWORD when required by your SMTP provider)."
        )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_address
    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    port = int(current_app.config.get("MAIL_PORT", 587))
    use_ssl = bool(current_app.config.get("MAIL_USE_SSL", False))
    use_tls = bool(current_app.config.get("MAIL_USE_TLS", not use_ssl))

    if use_ssl:
        with smtplib.SMTP_SSL(server_name, port, timeout=20) as smtp:
            if username:
                smtp.login(username, password or "")
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(server_name, port, timeout=20) as smtp:
            smtp.ehlo()
            if use_tls:
                smtp.starttls()
                smtp.ehlo()
            if username:
                smtp.login(username, password or "")
            smtp.send_message(msg)
