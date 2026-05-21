from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.core.permissions import manager_required

from .forms import (
    CARGO_NAME_SUGGESTIONS,
    CARGO_TYPE_SUGGESTIONS,
    ShipmentOrderCreateForm,
    ShipmentOrderEditForm,
)
from .models import ShipmentOrder


def _order_form_context(form, **extra):
    return {
        "form": form,
        "cargo_name_suggestions": CARGO_NAME_SUGGESTIONS,
        "cargo_type_suggestions": CARGO_TYPE_SUGGESTIONS,
        **extra,
    }


def _manager_orders_queryset(request):
    return (
        ShipmentOrder.objects.filter(manager=request.user)
        .select_related("transport", "manager", "trip")
        .prefetch_related("points__location", "route_options")
    )


def _can_cancel_order(order):
    return (
        order.status in {ShipmentOrder.Status.NEW, ShipmentOrder.Status.CALCULATED}
        and not hasattr(order, "trip")
    )


@manager_required
@require_http_methods(["GET"])
def order_list(request):
    orders = _manager_orders_queryset(request)
    selected_status = request.GET.get("status", "")
    valid_statuses = {choice.value for choice in ShipmentOrder.Status}
    if selected_status in valid_statuses:
        orders = orders.filter(status=selected_status)
    else:
        selected_status = ""

    return render(
        request,
        "orders/order_list.html",
        {
            "orders": orders,
            "selected_status": selected_status,
            "status_choices": ShipmentOrder.Status.choices,
        },
    )


@manager_required
@require_http_methods(["GET", "POST"])
def order_create(request):
    if request.method == "POST":
        form = ShipmentOrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(manager=request.user)
            messages.success(request, "Заявка создана.")
            return redirect("orders:detail", pk=order.pk)
    else:
        form = ShipmentOrderCreateForm()

    return render(request, "orders/order_create.html", _order_form_context(form))


@manager_required
@require_http_methods(["GET", "POST"])
def order_edit(request, pk):
    order = get_object_or_404(_manager_orders_queryset(request), pk=pk)
    if order.status != ShipmentOrder.Status.NEW:
        raise PermissionDenied

    points = list(order.points.all().order_by("sequence"))
    if len(points) < 2:
        raise PermissionDenied

    if request.method == "POST":
        form = ShipmentOrderEditForm(request.POST, instance=order, points_instance=points[:2])
        if form.is_valid():
            order = form.save()
            messages.success(request, "Заявка обновлена.")
            return redirect("orders:detail", pk=order.pk)
    else:
        form = ShipmentOrderEditForm(instance=order, points_instance=points[:2])

    return render(
        request,
        "orders/order_edit.html",
        _order_form_context(form, order=order),
    )


@manager_required
@require_http_methods(["GET"])
def order_detail(request, pk):
    order = get_object_or_404(_manager_orders_queryset(request), pk=pk)
    points = order.points.all().order_by("sequence")
    return render(
        request,
        "orders/order_detail.html",
        {"order": order, "points": points, "can_cancel_order": _can_cancel_order(order)},
    )


@manager_required
@require_http_methods(["POST"])
def order_cancel(request, pk):
    order = get_object_or_404(_manager_orders_queryset(request), pk=pk)
    if not _can_cancel_order(order):
        raise PermissionDenied

    order.status = ShipmentOrder.Status.CANCELLED
    order.save(update_fields=["status", "updated_at"])
    messages.success(request, "Заявка отменена.")
    return redirect("orders:detail", pk=order.pk)
