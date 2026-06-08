from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.fleet.models import Transport
from apps.locations.models import Location

from .models import OrderPoint, ShipmentOrder

CARGO_TYPE_SUGGESTIONS = (
    "Строительные материалы",
    "Металлоизделия",
    "Лесоматериалы",
    "Промышленные товары",
    "Продовольственные товары",
    "Сборный груз",
    "Легкий объемный груз",
    "Тяжеловесный груз",
    "Электротехнические товары",
    "Непродовольственные товары",
)

CARGO_NAME_SUGGESTIONS = (
    "Металлопрокат",
    "Арматура строительная",
    "Стальные трубы",
    "Кирпич строительный",
    "Бетонные блоки",
    "Цемент в мешках",
    "Сухие строительные смеси",
    "Пиломатериалы",
    "Паллетированный товар",
    "Бытовая техника",
    "Запчасти для оборудования",
    "Кабельная продукция",
)


class ShipmentOrderForm(forms.ModelForm):
    origin_location = forms.ModelChoiceField(
        label="Точка отправления",
        queryset=Location.objects.none(),
    )
    destination_location = forms.ModelChoiceField(
        label="Точка доставки",
        queryset=Location.objects.none(),
    )

    class Meta:
        model = ShipmentOrder
        fields = (
            "transport",
            "cargo_name",
            "cargo_type",
            "cargo_weight_kg",
            "desired_delivery_date",
            "notes",
        )
        labels = {
            "transport": "Транспорт",
            "cargo_name": "Наименование груза",
            "cargo_type": "Тип груза",
            "cargo_weight_kg": "Вес груза, кг",
            "desired_delivery_date": "Желаемая дата доставки",
            "notes": "Примечания",
        }
        widgets = {
            "cargo_name": forms.TextInput(
                attrs={
                    "autocomplete": "off",
                    "list": "cargo-name-suggestions",
                }
            ),
            "cargo_type": forms.TextInput(
                attrs={
                    "autocomplete": "off",
                    "list": "cargo-type-suggestions",
                }
            ),
            "desired_delivery_date": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d",
            ),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        self.points_instance = kwargs.pop("points_instance", None)
        super().__init__(*args, **kwargs)
        transports = Transport.objects.filter(is_active=True).select_related(
            "eco_standard"
        )
        self.fields["transport"].queryset = transports
        self.transport_capacity_data = {
            str(transport.pk): {
                "capacity_kg": transport.capacity_kg,
                "label": str(transport),
            }
            for transport in transports
        }
        active_locations = Location.objects.filter(is_active=True)
        self.fields["origin_location"].queryset = active_locations
        self.fields["destination_location"].queryset = active_locations
        if self.instance.pk and self.points_instance:
            origin, destination = self.points_instance
            self.fields["origin_location"].initial = origin.location_id
            self.fields["destination_location"].initial = destination.location_id

    def clean(self):
        cleaned_data = super().clean()
        transport = cleaned_data.get("transport")
        cargo_weight_kg = cleaned_data.get("cargo_weight_kg")
        origin_location = cleaned_data.get("origin_location")
        destination_location = cleaned_data.get("destination_location")
        desired_delivery_date = cleaned_data.get("desired_delivery_date")

        if desired_delivery_date and desired_delivery_date < timezone.localdate():
            self.add_error(
                "desired_delivery_date",
                "Желаемая дата доставки не может быть в прошлом.",
            )

        if transport and cargo_weight_kg and cargo_weight_kg > transport.capacity_kg:
            self.add_error(
                "cargo_weight_kg",
                "Вес груза превышает грузоподъемность выбранного транспорта.",
            )

        if origin_location and destination_location and origin_location == destination_location:
            raise ValidationError("Точка отправления и точка доставки должны различаться.")

        return cleaned_data

    def save(self, manager=None, commit=True):
        if not commit:
            raise ValueError("ShipmentOrderForm должен сохранять заявку сразу.")

        with transaction.atomic():
            order = super().save(commit=False)
            if manager is not None:
                order.manager = manager
            if not order.pk:
                order.status = ShipmentOrder.Status.NEW
            order.full_clean()
            order.save()
            self._save_points(order)
        return order

    def _save_points(self, order):
        origin_location = self.cleaned_data["origin_location"]
        destination_location = self.cleaned_data["destination_location"]
        origin_point, _created = OrderPoint.objects.update_or_create(
            order=order,
            sequence=1,
            defaults={
                "location": origin_location,
                "point_type": OrderPoint.PointType.PICKUP,
            },
        )
        destination_point, _created = OrderPoint.objects.update_or_create(
            order=order,
            sequence=2,
            defaults={
                "location": destination_location,
                "point_type": OrderPoint.PointType.DELIVERY,
            },
        )
        order.points.exclude(pk__in=[origin_point.pk, destination_point.pk]).delete()


class ShipmentOrderCreateForm(ShipmentOrderForm):
    pass


class ShipmentOrderEditForm(ShipmentOrderForm):
    pass
