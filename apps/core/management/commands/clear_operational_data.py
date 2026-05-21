from django.core.management.base import BaseCommand
from django.core.management.color import no_style
from django.db import connection, transaction

from apps.orders.models import OrderPoint, ShipmentOrder
from apps.routing.models import RouteOption
from apps.trips.models import Trip, TripStatusEvent

COUNT_MODELS = (
    ("ShipmentOrder", ShipmentOrder),
    ("OrderPoint", OrderPoint),
    ("RouteOption", RouteOption),
    ("Trip", Trip),
    ("TripStatusEvent", TripStatusEvent),
)

DELETE_MODELS = (
    ("TripStatusEvent", TripStatusEvent),
    ("Trip", Trip),
    ("RouteOption", RouteOption),
    ("OrderPoint", OrderPoint),
    ("ShipmentOrder", ShipmentOrder),
)

SEQUENCE_MODELS = (
    ShipmentOrder,
    OrderPoint,
    RouteOption,
    Trip,
    TripStatusEvent,
)


class Command(BaseCommand):
    help = (
        "Безопасно очищает операционные демо-данные EcoLogist: заявки, точки, "
        "варианты маршрутов, рейсы и события статусов."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Подтвердить удаление операционных данных.",
        )
        parser.add_argument(
            "--reset-sequences",
            action="store_true",
            help="После удаления сбросить sequences операционных таблиц.",
        )

    def handle(self, *args, **options):
        confirmed = options["yes"]
        reset_sequences = options["reset_sequences"]

        self.stdout.write(
            self.style.WARNING(
                "Внимание: команда предназначена только для локальной/демонстрационной "
                "очистки. Не используйте ее в production."
            )
        )
        self._write_counts("До удаления")

        if not confirmed:
            self.stdout.write(
                self.style.WARNING(
                    "Удаление не выполнено. Для запуска передайте флаг --yes."
                )
            )
            if reset_sequences:
                self.stdout.write(
                    self.style.WARNING(
                        "Сброс sequences не выполнен. Для запуска передайте флаг --yes."
                    )
                )
            return

        with transaction.atomic():
            for _label, model in DELETE_MODELS:
                model.objects.all().delete()
            if reset_sequences:
                self._reset_sequences()

        self.stdout.write(self.style.SUCCESS("Операционные данные удалены."))
        if reset_sequences:
            self.stdout.write(
                self.style.SUCCESS("Sequences операционных таблиц сброшены.")
            )
        self._write_counts("После удаления")

    def _write_counts(self, title):
        self.stdout.write(f"{title}:")
        for label, model in COUNT_MODELS:
            self.stdout.write(f"- {label}: {model.objects.count()}")

    def _reset_sequences(self):
        sql_statements = connection.ops.sequence_reset_sql(no_style(), SEQUENCE_MODELS)
        with connection.cursor() as cursor:
            for sql in sql_statements:
                cursor.execute(sql)
