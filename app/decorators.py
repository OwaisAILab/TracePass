
from functools import wraps
from flask import abort
from flask_login import current_user


#  Creates a decorator that blocks users who do not have one of the required roles.
def role_required(*role_names: str):
    """
    Restrict a view to users whose role is one of role_names.

    Usage:
        @app.route("/admin/users")
        @login_required
        @role_required("admin")
        def manage_users(): ...

    Always place @login_required ABOVE this decorator so anonymous users get
    redirected to login instead of a 403.
    """

# Implements the decorator operation used by this module.
    def decorator(view_func):
# Implements the wrapped operation used by this module.
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if not current_user.has_role(*role_names):
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator
