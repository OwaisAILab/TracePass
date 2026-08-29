from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.models.user import User
from app.models.role import Role, ROLE_CUSTOMER
from app.auth.forms import LoginForm, RegistrationForm

auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegistrationForm()
    if form.validate_on_submit():
        customer_role = Role.query.filter_by(name=ROLE_CUSTOMER).first()
        if customer_role is None:
            # Should never happen post-seed, but fail loudly rather than
            # creating a user with no role if the DB is in a bad state.
            flash("Registration is temporarily unavailable. Contact an administrator.", "danger")
            return render_template("auth/register.html", form=form)

        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            role_id=customer_role.id,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash("Account created. You can now log in.", "success")
        return redirect(url_for("main.index"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()

        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form=form)

        if not user.is_active:
            flash("This account has been deactivated. Contact an administrator.", "danger")
            return render_template("auth/login.html", form=form)

        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get("next")
        # Never redirect to an absolute/external URL from the `next` param —
        # open-redirect risk. Only allow relative paths.
        if not next_page or not next_page.startswith("/"):
            next_page = url_for("main.dashboard")
        return redirect(next_page)

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))
