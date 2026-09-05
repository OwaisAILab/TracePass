
from app import create_app
from app.extensions import db
from sqlalchemy import inspect
app=create_app()
with app.app_context():
    print("Database:", app.config.get("SQLALCHEMY_DATABASE_URI"))
    tables=inspect(db.engine).get_table_names()
    print("users table:", "OK" if "users" in tables else "MISSING")
    print("Tables:", ", ".join(sorted(tables)) if tables else "(none)")
