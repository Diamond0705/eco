from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.core.permissions import manager_required

from .forms import ShipmentOrderCreateForm, ShipmentOrderEditForm
from .models import ShipmentOrder


def _manager_orders_queryset(request):
    return (
        ShipmentOrder.objects.filter(manager=request.user)
        .select_related("transport", "manager")
        .prefetch_related("points__location")
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

    return render(request, "orders/order_create.html", {"form": form})


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

    return render(request, "orders/order_edit.html", {"form": form, "order": order})


@manager_required
@require_http_methods(["GET"])
def order_detail(request, pk):
    order = get_object_or_404(_manager_orders_queryset(request), pk=pk)
    points = order.points.all().order_by("sequence")
    return render(request, "orders/order_detail.html", {"order": order, "points": points})


@manager_required
@require_http_methods(["POST"])
def order_cancel(request, pk):
    order = get_object_or_404(_manager_orders_queryset(request), pk=pk)
    if order.status != ShipmentOrder.Status.NEW:
        raise PermissionDenied

    order.status = ShipmentOrder.Status.CANCELLED
    order.save(update_fields=["status", "updated_at"])
    messages.success(request, "Заявка отменена.")
    return redirect("orders:detail", pk=order.pk)
