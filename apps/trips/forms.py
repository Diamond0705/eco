from django import forms
from django.utils import timezone

DATETIME_LOCAL_FORMAT = "%Y-%m-%dT%H:%M"


class TripStartForm(forms.Form):
    actual_start_at = forms.DateTimeField(
        label="Фактическое начало",
        input_formats=[DATETIME_LOCAL_FORMAT],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format=DATETIME_LOCAL_FORMAT,
        ),
    )
    comment = forms.CharField(
        label="Комментарий",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class TripDeliverForm(forms.Form):
    actual_finish_at = forms.DateTimeField(
        label="Фактическое завершение",
        input_formats=[DATETIME_LOCAL_FORMAT],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"},
            format=DATETIME_LOCAL_FORMAT,
        ),
    )
    comment = forms.CharField(
        label="Комментарий",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


def datetime_local_initial(value=None):
    value = timezone.localtime(value or timezone.now())
    return value.strftime(DATETIME_LOCAL_FORMAT)
