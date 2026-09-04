# PRESENTATION NOTE: This file is commented to make the project easier to explain during the final committee presentation.
"""Tests for the public Contact Us -> organizational account request workflow."""


# What this code does: Automated test that verifies the expected behavior of registration request routes are registered.
def test_registration_request_routes_are_registered(app):
    """The public request page and admin review endpoints must exist."""
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/contact" in rules
    assert "/admin/registration-requests" in rules
    assert "/admin/registration-requests/<int:request_id>" in rules
