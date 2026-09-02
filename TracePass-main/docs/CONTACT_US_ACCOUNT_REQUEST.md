# Contact Us → Request an Account

## Purpose
TracePass uses controlled registration for organizational users. Customers may use public self-registration, while manufacturers, suppliers, distributors, retailers and auditors must request access through **Contact Us**.

## Workflow
1. Visitor opens **Contact Us** on the public landing page.
2. Visitor selects the requested organizational role and enters applicant/organization information.
3. Visitor submits a password which is stored only as a password hash.
4. A `RegistrationRequest` is created with status `pending`.
5. Active administrators receive an in-app notification.
6. Admin opens **Administration → Registration Requests**.
7. Admin reviews the applicant and organization.
8. On approval, the organization is created or matched by registration number, marked verified, and the requested user account is created.
9. On rejection, the request remains stored with the administrator's reason.
10. The approval/rejection lifecycle is covered by the application's audit logging.

## Security decision
The request form does **not** create a privileged account immediately. This prevents a visitor from self-declaring a manufacturer/supplier/auditor identity and entering internal workflows without administrative verification.

## Database
The workflow uses the `registration_requests` table. Migration:

`c4d5e6f7a890_registration_requests.py`

The migration follows the existing `b1c2d3e4f567` industry-image migration, leaving a single migration head.

## Presentation answer
> “Customers can self-register for public verification. Organizational roles are controlled: a manufacturer, supplier, distributor, retailer or auditor submits an account request through Contact Us. The administrator verifies the organization and approves the request before the system creates the role-based account.”
