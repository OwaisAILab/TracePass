import io
import json
from app.extensions import db
from app.models.role import Role, ROLE_ADMIN, ROLE_CUSTOMER, ROLE_SUPPLIER
from app.models.user import User
from app.models.email_otp import EmailOTP, OTP_PURPOSE_CUSTOMER_REGISTRATION, OTP_PURPOSE_ORG_REQUEST
from app.models.registration_request import RegistrationRequest, REQUEST_PENDING, REQUEST_APPROVED
from app.models.registration_request_document import RegistrationRequestDocument
from app.models.notification import Notification


def test_customer_registration_creates_otp_and_redirects(client, app):
    """Customer registration should create an OTP record and redirect to /verify-otp without creating User immediately."""
    with app.app_context():
        response = client.post(
            "/register",
            data={
                "name": "Jane Customer",
                "email": "jane@example.com",
                "password": "Password123!",
                "confirm_password": "Password123!",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert response.location.endswith("/verify-otp")

        # User is not yet created in the DB
        assert User.query.filter_by(email="jane@example.com").first() is None

        # EmailOTP record was generated
        otp_record = EmailOTP.query.filter_by(
            email="jane@example.com",
            purpose=OTP_PURPOSE_CUSTOMER_REGISTRATION,
            is_used=False,
        ).first()
        assert otp_record is not None
        assert len(otp_record.otp_code) == 6


def test_customer_otp_verification_creates_user_and_allows_login(client, app):
    """Submitting the correct OTP should create the User account and allow authentication."""
    with app.app_context():
        # Step 1: Submit registration
        client.post(
            "/register",
            data={
                "name": "Jane Customer",
                "email": "jane2@example.com",
                "password": "Password123!",
                "confirm_password": "Password123!",
            },
            follow_redirects=True,
        )

        otp_record = EmailOTP.query.filter_by(
            email="jane2@example.com",
            purpose=OTP_PURPOSE_CUSTOMER_REGISTRATION,
            is_used=False,
        ).first()
        assert otp_record is not None
        code = otp_record.otp_code

        # Step 2: Submit OTP verification
        verify_response = client.post(
            "/verify-otp",
            data={"otp_code": code},
            follow_redirects=True,
        )
        assert verify_response.status_code == 200
        assert b"Email verified successfully" in verify_response.data

        # Verify User now exists
        user = User.query.filter_by(email="jane2@example.com").first()
        assert user is not None
        assert user.name == "Jane Customer"
        assert user.role.name == ROLE_CUSTOMER
        assert user.check_password("Password123!")

        # Verify OTP is marked used
        updated_otp = EmailOTP.query.get(otp_record.id)
        assert updated_otp.is_used is True


def test_customer_otp_verification_rejects_invalid_code(client, app):
    """Submitting an invalid OTP should show an error and keep the account uncreated."""
    with app.app_context():
        client.post(
            "/register",
            data={
                "name": "Invalid Customer",
                "email": "invalid@example.com",
                "password": "Password123!",
                "confirm_password": "Password123!",
            },
            follow_redirects=True,
        )

        # Submit wrong OTP
        verify_response = client.post(
            "/verify-otp",
            data={"otp_code": "000000"},
            follow_redirects=True,
        )
        assert verify_response.status_code == 200
        assert b"Incorrect verification code" in verify_response.data or b"attempt" in verify_response.data

        # User is still not created
        assert User.query.filter_by(email="invalid@example.com").first() is None


def test_customer_resend_otp(client, app):
    """Resending OTP should invalidate prior active code and issue a fresh 6-digit code."""
    with app.app_context():
        client.post(
            "/register",
            data={
                "name": "Resend Customer",
                "email": "resend@example.com",
                "password": "Password123!",
                "confirm_password": "Password123!",
            },
            follow_redirects=True,
        )

        first_otp = EmailOTP.query.filter_by(
            email="resend@example.com",
            purpose=OTP_PURPOSE_CUSTOMER_REGISTRATION,
            is_used=False,
        ).first()
        assert first_otp is not None

        # Call resend
        resend_response = client.post("/resend-otp", follow_redirects=True)
        assert resend_response.status_code == 200

        # Prior OTP is marked used/invalidated
        db.session.refresh(first_otp)
        assert first_otp.is_used is True

        # New active OTP exists
        new_otp = EmailOTP.query.filter_by(
            email="resend@example.com",
            purpose=OTP_PURPOSE_CUSTOMER_REGISTRATION,
            is_used=False,
        ).first()
        assert new_otp is not None
        assert new_otp.id != first_otp.id


def test_organizational_request_otp_flow_and_admin_forwarding(client, app, admin):
    """Organizational requests should require OTP email validation before dispatching admin notifications."""
    with app.app_context():
        # Step 1: Submit contact form with authenticity document
        data = {
            "name": "Alice Supplier",
            "email": "alice@supplier.example",
            "phone": "+123456789",
            "requested_role": "supplier",
            "organization_name": "Supplier Corp Ltd",
            "registration_no": "REG-SUP-101",
            "organization_email": "info@supplier.example",
            "organization_phone": "+123456780",
            "address": "Industrial Zone 1",
            "password": "SecurePassword1!",
            "confirm_password": "SecurePassword1!",
            "reason": "We supply cotton materials.",
            "authenticity_documents": (io.BytesIO(b"%PDF-1.4 mock pdf"), "certificate.pdf"),
        }
        response = client.post("/contact", data=data, content_type="multipart/form-data", follow_redirects=False)
        assert response.status_code == 302
        assert response.location.endswith("/contact/verify-otp")

        # Request exists but is NOT email verified yet
        req = RegistrationRequest.query.filter_by(email="alice@supplier.example").first()
        assert req is not None
        assert req.is_email_verified is False

        # Admin notifications must NOT be created before OTP validation
        notifications = Notification.query.filter_by(notif_type="account_request").all()
        assert len(notifications) == 0

        # OTP record exists
        otp_record = EmailOTP.query.filter_by(
            email="alice@supplier.example",
            purpose=OTP_PURPOSE_ORG_REQUEST,
            is_used=False,
        ).first()
        assert otp_record is not None

        # Step 2: Submit OTP validation
        verify_response = client.post(
            "/contact/verify-otp",
            data={"otp_code": otp_record.otp_code},
            follow_redirects=True,
        )
        assert verify_response.status_code == 200
        assert b"Your email has been verified" in verify_response.data

        # Request is now marked as email verified
        db.session.refresh(req)
        assert req.is_email_verified is True

        # Notifications have now been forwarded to the administrator
        notifications_after = Notification.query.filter_by(notif_type="account_request").all()
        assert len(notifications_after) >= 1
        assert "Alice Supplier" in notifications_after[0].message
        assert "Email Verified" in notifications_after[0].message
