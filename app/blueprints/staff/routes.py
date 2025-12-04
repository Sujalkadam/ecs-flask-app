from functools import wraps

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ...services import (
    StaffService,
    AssignmentService,
    RequestService,
    FeedbackService,
)
from . import staff_bp
from .forms import FeedbackForm, StaffLoginForm, StaffRegisterForm, StaffRequestItemForm


def staff_only(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or getattr(current_user, "user_role", "") != "staff":
            flash("Please log in as staff to continue.", "warning")
            return redirect(url_for("staff.login"))
        return view(*args, **kwargs)

    return wrapped


@staff_bp.route("/")
@login_required
@staff_only
def dashboard():
    assignments = AssignmentService.get_assignments_for_staff(current_user.id)
    outstanding_requests = RequestService.get_requests_for_staff(current_user.id)
    form = StaffRequestItemForm()
    feedback_form = FeedbackForm()
    return render_template(
        "staff/dashboard.html",
        assignments=assignments,
        form=form,
        requests=outstanding_requests,
        feedback_form=feedback_form,
    )


@staff_bp.route("/requests", methods=["POST"])
@login_required
@staff_only
def submit_request():
    form = StaffRequestItemForm()
    if form.validate_on_submit():
        try:
            RequestService.create_request(
                current_user.id,
                form.item_name.data,
                form.justification.data,
            )
            current_app.logger.info(
                "Staff request submitted",
                extra={"staff_id": current_user.id, "item_name": form.item_name.data},
            )
            flash("Request submitted. Admin will review shortly.", "success")
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            current_app.logger.error(f"Error submitting request: {str(e)}")
            flash("An error occurred while submitting the request.", "danger")
    else:
        current_app.logger.warning(
            "Staff request failed validation",
            extra={"staff_id": current_user.id, "errors": form.errors},
        )
        flash("Please fix the errors and try again.", "danger")

    return redirect(url_for("staff.dashboard"))


@staff_bp.route("/feedback", methods=["POST"])
@login_required
@staff_only
def submit_feedback():
    form = FeedbackForm()
    if form.validate_on_submit():
        try:
            FeedbackService.submit_feedback(
                current_user.id,
                form.rating.data,
                form.question_1.data,
                form.question_2.data,
                form.question_3.data,
                form.question_4.data,
                form.question_5.data,
            )
            current_app.logger.info(
                "Feedback submitted",
                extra={"staff_id": current_user.id, "rating": form.rating.data},
            )
            flash("Thank you for your feedback!", "success")
            return redirect(url_for("staff.thank_you"))
        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            current_app.logger.error(f"Error submitting feedback: {str(e)}")
            flash("An error occurred while submitting feedback.", "danger")
    else:
        current_app.logger.warning(
            "Feedback submission failed",
            extra={"staff_id": current_user.id, "errors": form.errors},
        )
        flash("Please complete all fields before submitting feedback.", "danger")
    return redirect(url_for("staff.dashboard"))


@staff_bp.route("/feedback/thanks")
@login_required
@staff_only
def thank_you():
    return render_template("staff/thank_you.html")


@staff_bp.route("/assignments/<int:assignment_id>/return", methods=["POST"])
@login_required
@staff_only
def request_return(assignment_id: int):
    try:
        AssignmentService.request_return(assignment_id, current_user.id)
        current_app.logger.info(
            "Return requested",
            extra={"assignment_id": assignment_id, "staff_id": current_user.id},
        )
        flash("Return request sent.", "info")
    except ValueError as e:
        flash(str(e), "warning" if "already" in str(e).lower() else "info")
    except Exception as e:
        current_app.logger.error(f"Error requesting return: {str(e)}")
        flash("An error occurred while requesting return.", "danger")

    return redirect(url_for("staff.dashboard"))


@staff_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated and getattr(current_user, "user_role", "") == "staff":
        return redirect(url_for("staff.dashboard"))

    form = StaffRegisterForm()
    if form.validate_on_submit():
        try:
            staff = StaffService.register(
                form.full_name.data,
                form.email.data,
                form.password.data,
                form.department.data,
            )
            login_user(staff)
            flash("Welcome to your workspace!", "success")
            return redirect(url_for("staff.dashboard"))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template("staff/register.html", form=form)


@staff_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated and getattr(current_user, "user_role", "") == "staff":
        return redirect(url_for("staff.dashboard"))

    form = StaffLoginForm()
    if form.validate_on_submit():
        staff = StaffService.authenticate(form.email.data, form.password.data)
        if not staff:
            flash("Invalid credentials. Try again.", "danger")
        else:
            login_user(staff)
            flash("Signed in successfully.", "success")
            return redirect(url_for("staff.dashboard"))

    return render_template("staff/login.html", form=form)


@staff_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Signed out.", "info")
    return redirect(url_for("public.role_selection"))

