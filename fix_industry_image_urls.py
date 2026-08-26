# TracePass code note: This module implements the fix_industry_image_urls.py part of the application.
"""
One-time fix for industries whose image_url was saved before the /admin
routing fix (they were stored as /uploads/industry_images/<file> instead of
/admin/uploads/industry_images/<file>, causing a broken-image icon).

Run this once after updating your code:
    python fix_industry_image_urls.py
"""
from app import create_app
from app.extensions import db
from app.models.industry import Industry

app = create_app("development")

with app.app_context():
    OLD_PREFIX = "/uploads/industry_images/"
    NEW_PREFIX = "/admin/uploads/industry_images/"

    fixed = 0
    for industry in Industry.query.all():
        if industry.image_url and industry.image_url.startswith(OLD_PREFIX):
            industry.image_url = NEW_PREFIX + industry.image_url[len(OLD_PREFIX):]
            fixed += 1

    if fixed:
        db.session.commit()
    print(f"Fixed {fixed} industry image URL(s).")
