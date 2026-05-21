from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms.models import construct_instance

from apps.fleet.models import EcoCalculationSettings, EcoStandard, Transport
from apps.locations.models import Location

User = get_user_model()


def active_status_field():
    return forms.TypedChoiceField(
        label="Активность",
        choices=(("1", "Активен"), ("0", "Неактивен")),
        coerce=lambda value: value == "1",
        widget=forms.RadioSelect(attrs={"class": "status-radio-input"}),
    )


def active_status_select_field():
    return forms.TypedChoiceField(
        label="Активность",
        choices=(("1", "Активен"), ("0", "Неактивен")),
        coerce=lambda value: value == "1",
        widget=forms.RadioSelect(attrs={"class": "status-radio-input"}),
    )


def set_active_initial(form):
    if form.is_bound or "is_active" not in form.fields:
        return
    is_active = form.initial.get("is_active", getattr(form.instance, "is_active", True))
    form.initial["is_active"] = "1" if is_active else "0"


class AdminUserForm(forms.ModelForm):
    is_active = active_status_select_field()

    class Meta:
        model = User
        fields = ("is_active",)

    def __init__(self, *args, current_user=None, **kwargs):
        self.current_user = current_user
        super().__init__(*args, **kwargs)
        set_active_initial(self)


class TransportForm(forms.ModelForm):
    is_active = active_status_field()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_active_initial(self)

    class Meta:
        model = Transport
        fields = (
            "plate_number",
            "model",
            "category",
            "fuel_type",
            "capacity_kg",
            "fuel_consumption_l_per_100km",
            "eco_standard",
            "year",
            "is_active",
        )
        labels = {
            "plate_number": "Госномер",
            "model": "Модель",
            "category": "Категория",
            "fuel_type": "Тип топлива",
            "capacity_kg": "Грузоподъемность, кг",
            "fuel_consumption_l_per_100km": "Расход топлива, л/100 км",
            "eco_standard": "Экологический стандарт",
            "year": "Год выпуска",
            "is_active": "Активность",
        }


class LocationForm(forms.ModelForm):
    is_active = active_status_field()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_active_initial(self)

    class Meta:
        model = Location
        fields = ("name", "address", "latitude", "longitude", "is_active")
        labels = {
            "name": "Название",
            "address": "Адрес",
            "latitude": "Широта",
            "longitude": "Долгота",
            "is_active": "Активность",
        }


class EcoStandardForm(forms.ModelForm):
    is_active = active_status_field()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_active_initial(self)

    class Meta:
        model = EcoStandard
        fields = ("name", "nox_limit_g_per_kwh", "pm_limit_mg_per_kwh", "is_active")
        labels = {
            "name": "Название",
            "nox_limit_g_per_kwh": "NOx, г/кВт·ч",
            "pm_limit_mg_per_kwh": "PM, мг/кВт·ч",
            "is_active": "Активность",
        }


class EcoCalculationSettingsForm(forms.ModelForm):
    is_active = forms.TypedChoiceField(
        label="Активность",
        choices=(("1", "Активны"), ("0", "Неактивны")),
        coerce=lambda value: value == "1",
        widget=forms.RadioSelect(attrs={"class": "status-radio-input"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_active_initial(self)

    class Meta:
        model = EcoCalculationSettings
        fields = (
            "name",
            "is_active",
            "fuel_price_rub_per_liter",
            "service_tariff_rub_per_km",
            "driver_time_tariff_rub_per_hour",
            "diesel_co2_kg_per_liter",
            "engine_work_kwh_per_km",
            "full_load_fuel_increase_percent",
            "co2_weight",
            "nox_weight",
            "pm_weight",
            "co2_critical_kg",
            "nox_critical_g",
            "pm_critical_g",
        )
        labels = {
            "name": "Название",
            "is_active": "Активность",
            "fuel_price_rub_per_liter": "Цена топлива, руб/л",
            "service_tariff_rub_per_km": "Сервисный тариф, руб/км",
            "driver_time_tariff_rub_per_hour": "Тариф времени водителя, руб/ч",
            "diesel_co2_kg_per_liter": "CO2 дизеля, кг/л",
            "engine_work_kwh_per_km": "Работа двигателя, кВт·ч/км",
            "full_load_fuel_increase_percent": "Рост расхода при полной загрузке, %",
            "co2_weight": "Вес CO2",
            "nox_weight": "Вес NOx",
            "pm_weight": "Вес PM",
            "co2_critical_kg": "Критический CO2, кг",
            "nox_critical_g": "Критический NOx, г",
            "pm_critical_g": "Критический PM, г",
    }

    def _post_clean(self):
        exclude = self._get_validation_exclusions()

        try:
            self.instance = construct_instance(
                self,
                self.instance,
                self._meta.fields,
                self._meta.exclude,
            )
        except ValidationError as error:
            self._update_errors(error)

        try:
            self.instance.full_clean(
                exclude=exclude,
                validate_unique=False,
                validate_constraints=False,
            )
        except ValidationError as error:
            self._update_errors(error)

        if self._validate_unique:
            self.validate_unique()
