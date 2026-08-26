# TracePass code note: This module implements the app/reporting/audit.py part of the application.
"""
Automatic audit logging.

Rather than requiring every route to remember to call an audit_log() helper,
this hooks SQLAlchemy's mapper-level after_insert / after_update / after_delete
events directly onto the models we care about. Once register_audit_listeners()
is called at app startup, every create/update/delete of an audited model is
logged with zero per-route effort — coverage can't accidentally be missed.

Implementation note: we write via `connection.execute()` against the raw
audit_logs table rather than `session.add()`. Doing it through the ORM
Session here would re-trigger autoflush/flush-planning while a flush is
already in progress, which is exactly the kind of recursive-flush bug this
pattern is designed to avoid. Writing straight to the connection sidesteps
that entirely — this is the standard approach for SQLAlchemy audit logging.
"""

import json
from datetime import datetime, timezone
from sqlalchemy import event, inspect as sa_inspect
from flask import has_request_context
from flask_login import current_user

from app.models.audit_log import AuditLog

# Columns we never want to write into an audit log, even serialized.
SENSITIVE_COLUMNS = {"password_hash"}

_listeners_registered = False


# Code explanation: Implement the `current user id` operation used by this part of TracePass.
def _current_user_id():
    if not has_request_context():
        return None
    try:
        if current_user.is_authenticated:
            return current_user.id
    except Exception:
        pass
    return None


# Code explanation: Implement the `safe snapshot` operation used by this part of TracePass.
def _safe_snapshot(target):
    """Serializes a model instance's plain columns (not relationships) to a dict."""
    mapper = sa_inspect(target).mapper
    data = {}
    for column in mapper.columns:
        if column.key in SENSITIVE_COLUMNS:
            continue
        data[column.key] = getattr(target, column.key, None)
    return json.dumps(data, default=str)


# Code explanation: Implement the `write log` operation used by this part of TracePass.
def _write_log(connection, target, action):
    connection.execute(
        AuditLog.__table__.insert(),
        {
            "user_id": _current_user_id(),
            "action": action,
            "entity_type": target.__class__.__name__,
            "entity_id": getattr(target, "id", None),
            "old_value": _safe_snapshot(target) if action == "delete" else None,
            "new_value": _safe_snapshot(target) if action != "delete" else None,
            "created_at": datetime.now(timezone.utc),
        },
    )


# Code explanation: Implement the `register audit listeners` operation used by this part of TracePass.
def register_audit_listeners(models_to_audit):
    """
    Call once at app startup with the list of model CLASSES to audit.
    Guarded against double-registration (create_app() may run more than
    once in the same process, e.g. across tests).
    """
    global _listeners_registered
    if _listeners_registered:
        return

    for model in models_to_audit:
        event.listens_for(model, "after_insert")(
            lambda mapper, connection, target: _write_log(connection, target, "create")
        )
        event.listens_for(model, "after_update")(
            lambda mapper, connection, target: _write_log(connection, target, "update")
        )
        event.listens_for(model, "after_delete")(
            lambda mapper, connection, target: _write_log(connection, target, "delete")
        )

    _listeners_registered = True
