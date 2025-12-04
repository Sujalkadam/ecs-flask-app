from functools import wraps

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ...services import (
    AdminService,
    InventoryService,
    RequestService,
    AssignmentService,
    StaffService,
    FeedbackService,
)
from . import admin_bp
from .forms import (
    AdminLoginForm,
    AdminRegisterForm,
    ApproveRequestForm,
    CompleteReturnForm,
    DeleteItemForm,
    InventoryForm,
    ManualAssignmentForm,
    RejectRequestForm,
)


def admin_only(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or getattr(current_user, "user_role", "") != "admin":
            flash("Please log in as admin to continue.", "warning")
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)

    return wrapped


@admin_bp.route("/")
@login_required
@admin_only
def dashboard():
    stats = AdminService.get_dashboard_stats()
    latest_items = InventoryService.get_latest_items(3)
    return render_template(
        "admin/dashboard.html",
        latest_items=latest_items,
        inventory_count=stats["inventory_count"],
        inventory_quantity=stats["inventory_quantity"],
        pending_requests=stats["pending_requests"],
        pending_returns=stats["pending_returns"],
    )


@admin_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated and getattr(current_user, "user_role", "") == "admin":
        return redirect(url_for("admin.dashboard"))

    form = AdminRegisterForm()
    if form.validate_on_submit():
        try:
            admin = AdminService.register(
                form.full_name.data,
                form.email.data,
                form.password.data,
            )
            login_user(admin)
            flash("Admin workspace ready. Welcome!", "success")
            return redirect(url_for("admin.dashboard"))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template("admin/register.html", form=form)


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated and getattr(current_user, "user_role", "") == "admin":
        return redirect(url_for("admin.dashboard"))

    form = AdminLoginForm()
    if form.validate_on_submit():
        admin = AdminService.authenticate(form.email.data, form.password.data)
        if not admin:
            flash("Invalid credentials. Try again.", "danger")
        else:
            login_user(admin)
            flash("Signed in successfully.", "success")
            return redirect(url_for("admin.dashboard"))

    return render_template("admin/login.html", form=form)


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Signed out.", "info")
    return redirect(url_for("public.role_selection"))


@admin_bp.route("/requests")
@login_required
@admin_only
def requests_queue():
    pending_requests = RequestService.get_pending_requests()
    request_history = RequestService.get_request_history(10)
    returns_queue = AssignmentService.get_pending_returns()

    item_choices = InventoryService.get_available_items_for_choices()
    approve_forms = {}
    reject_forms = {}
    for req in pending_requests:
        approve_form = ApproveRequestForm(prefix=f"approve-{req.id}")
        approve_form.item_id.choices = item_choices
        approve_form.request_id.data = req.id
        approve_forms[req.id] = approve_form

        reject_form = RejectRequestForm(prefix=f"reject-{req.id}")
        reject_form.request_id.data = req.id
        reject_forms[req.id] = reject_form

    return_forms = {}
    for assignment in returns_queue:
        return_form = CompleteReturnForm(prefix=f"return-{assignment.id}")
        return_form.assignment_id.data = assignment.id
        return_forms[assignment.id] = return_form

    manual_form = ManualAssignmentForm()
    manual_form.item_id.choices = item_choices
    manual_form.staff_id.choices = StaffService.get_staff_for_choices()

    return render_template(
        "admin/requests.html",
        pending_requests=pending_requests,
        request_history=request_history,
        returns_queue=returns_queue,
        approve_forms=approve_forms,
        reject_forms=reject_forms,
        return_forms=return_forms,
        manual_form=manual_form,
        has_inventory=bool(item_choices),
    )


@admin_bp.route("/requests/<int:request_id>/approve", methods=["POST"])
@login_required
@admin_only
def approve_request(request_id: int):
    form = ApproveRequestForm(prefix=f"approve-{request_id}")
    form.item_id.choices = InventoryService.get_available_items_for_choices()
    if not form.validate_on_submit() or int(form.request_id.data) != request_id:
        current_app.logger.warning(
            "Approve request failed validation",
            extra={"request_id": request_id, "errors": form.errors},
        )
        flash("Could not process request approval. Please recheck the form.", "danger")
        return redirect(url_for("admin.requests_queue"))

    try:
        result = RequestService.approve_request(request_id, form.item_id.data)
        current_app.logger.info(
            "Request approved",
            extra={
                "request_id": request_id,
                "item_id": form.item_id.data,
                "staff_id": result["request"].staff_id,
            },
        )
        flash("Request approved and item assigned.", "success")
    except ValueError as e:
        flash(str(e), "warning")
    except Exception as e:
        current_app.logger.error(f"Error approving request: {str(e)}")
        flash("An error occurred while approving the request.", "danger")

    return redirect(url_for("admin.requests_queue"))


@admin_bp.route("/requests/<int:request_id>/reject", methods=["POST"])
@login_required
@admin_only
def reject_request(request_id: int):
    form = RejectRequestForm(prefix=f"reject-{request_id}")
    if not form.validate_on_submit() or int(form.request_id.data) != request_id:
        current_app.logger.warning(
            "Reject request failed validation",
            extra={"request_id": request_id, "errors": form.errors},
        )
        flash("Could not reject the request. Please retry.", "danger")
        return redirect(url_for("admin.requests_queue"))

    try:
        request_record = RequestService.reject_request(request_id)
        current_app.logger.info(
            "Request rejected",
            extra={"request_id": request_id, "staff_id": request_record.staff_id},
        )
        flash("Request rejected.", "info")
    except ValueError as e:
        flash(str(e), "info")
    except Exception as e:
        current_app.logger.error(f"Error rejecting request: {str(e)}")
        flash("An error occurred while rejecting the request.", "danger")

    return redirect(url_for("admin.requests_queue"))


@admin_bp.route("/assignments/manual", methods=["POST"])
@login_required
@admin_only
def manual_assignment():
    form = ManualAssignmentForm()
    form.item_id.choices = InventoryService.get_available_items_for_choices()
    form.staff_id.choices = StaffService.get_staff_for_choices()
    if not form.validate_on_submit():
        current_app.logger.warning(
            "Manual assignment failed validation", extra={"errors": form.errors}
        )
        flash("Could not create manual assignment. Check the selections.", "danger")
        return redirect(url_for("admin.requests_queue"))

    try:
        assignment = AssignmentService.create_assignment(
            form.item_id.data,
            form.staff_id.data,
        )
        item = InventoryService.get_item(form.item_id.data)
        staff = StaffService.get_staff(form.staff_id.data)
        current_app.logger.info(
            "Manual assignment created",
            extra={"item_id": item.id, "staff_id": staff.id},
        )
        flash(f"{item.name} assigned to {staff.full_name}.", "success")
    except ValueError as e:
        flash(str(e), "warning")
    except Exception as e:
        current_app.logger.error(f"Error creating manual assignment: {str(e)}")
        flash("An error occurred while creating the assignment.", "danger")

    return redirect(url_for("admin.requests_queue"))


@admin_bp.route("/assignments/<int:assignment_id>/complete-return", methods=["POST"])
@login_required
@admin_only
def complete_return(assignment_id: int):
    form = CompleteReturnForm(prefix=f"return-{assignment_id}")
    if not form.validate_on_submit() or int(form.assignment_id.data) != assignment_id:
        current_app.logger.warning(
            "Return completion failed validation",
            extra={"assignment_id": assignment_id, "errors": form.errors},
        )
        flash("Could not process return. Please retry.", "danger")
        return redirect(url_for("admin.requests_queue"))

    try:
        assignment = AssignmentService.complete_return(assignment_id)
        current_app.logger.info(
            "Return completed",
            extra={"assignment_id": assignment_id, "item_id": assignment.item_id},
        )
        flash("Return completed and inventory updated.", "success")
    except ValueError as e:
        flash(str(e), "info")
    except Exception as e:
        current_app.logger.error(f"Error completing return: {str(e)}")
        flash("An error occurred while processing the return.", "danger")

    return redirect(url_for("admin.requests_queue"))


@admin_bp.route("/reports")
@login_required
@admin_only
def reports():
    feedback_stats = FeedbackService.get_stats()
    recent_feedback = FeedbackService.get_recent_feedback(10)
    low_stock = InventoryService.get_low_stock_items(3)
    active_assignments = AssignmentService.get_active_assignments_count()
    return render_template(
        "admin/reports.html",
        avg_rating=feedback_stats["average_rating"],
        total_feedback=feedback_stats["total_feedback"],
        recent_feedback=recent_feedback,
        low_stock=low_stock,
        active_assignments=active_assignments,
    )


@admin_bp.route("/inventory")
@login_required
@admin_only
def inventory():
    search_query = request.args.get("q", "").strip()
    items = InventoryService.list_items(search_query if search_query else None)
    stats = InventoryService.get_stats()
    delete_form = DeleteItemForm()
    return render_template(
        "admin/inventory_list.html",
        items=items,
        search_query=search_query,
        stats=stats,
        delete_form=delete_form,
    )


@admin_bp.route("/inventory/new", methods=["GET", "POST"])
@login_required
@admin_only
def inventory_create():
    form = InventoryForm()
    if form.validate_on_submit():
        try:
            InventoryService.create_item(
                form.name.data,
                form.category.data,
                form.quantity.data,
                form.purchase_date.data,
                form.price.data,
            )
            flash("Inventory item added.", "success")
            return redirect(url_for("admin.inventory"))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template(
        "admin/inventory_form.html",
        form=form,
        mode="create",
    )


@admin_bp.route("/inventory/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
@admin_only
def inventory_edit(item_id: int):
    item = InventoryService.get_item(item_id)
    if not item:
        abort(404)
    
    form = InventoryForm(obj=item)
    if form.validate_on_submit():
        try:
            InventoryService.update_item(
                item_id,
                form.name.data,
                form.category.data,
                form.quantity.data,
                form.purchase_date.data,
                form.price.data,
            )
            flash("Inventory item updated.", "success")
            return redirect(url_for("admin.inventory"))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template(
        "admin/inventory_form.html",
        form=form,
        mode="edit",
        item=item,
    )


@admin_bp.route("/inventory/<int:item_id>/delete", methods=["POST"])
@login_required
@admin_only
def inventory_delete(item_id: int):
    form = DeleteItemForm()
    if not form.validate_on_submit():
        abort(400)
    
    try:
        InventoryService.delete_item(item_id)
        flash("Inventory item removed.", "info")
    except Exception as e:
        current_app.logger.error(f"Error deleting item: {str(e)}")
        flash("An error occurred while deleting the item.", "danger")
    
    return redirect(url_for("admin.inventory"))

