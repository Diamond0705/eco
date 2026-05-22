from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.fleet.models import EcoStandard, Transport
from apps.locations.models import Location
from apps.orders.models import OrderPoint, ShipmentOrder
from apps.reports.models import ArchivedDocument
from apps.reports.services.document_archive import DocumentArchiveService
from apps.routing.services.route_calculation_service import RouteCalculationService
from apps.trips.models import Trip
from apps.trips.services import TripLifecycleService

User = get_user_model()
XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@pytest.fixture(autouse=True)
def local_archive_storage(settings, tmp_path):
    settings.USE_S3_STORAGE = False
    settings.DOCUMENT_ARCHIVE_ENABLED = True
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.MEDIA_URL = "/media/"


@pytest.fixture
def manager():
    return User.objects.create_user(
        username="archive_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def other_manager():
    return User.objects.create_user(
        username="archive_other_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        username="archive_admin",
        password="StrongPass12345",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def transport():
    standard = EcoStandard.objects.create(
        name="Euro VI",
        nox_limit_g_per_kwh=Decimal("0.46"),
        pm_limit_mg_per_kwh=Decimal("10.00"),
    )
    return Transport.objects.create(
        plate_number="А777АА777",
        model="КАМАЗ 5490",
        category=Transport.Category.N3,
        capacity_kg=20000,
        fuel_consumption_l_per_100km=Decimal("29.00"),
        eco_standard=standard,
        year=2021,
    )


@pytest.fixture
def locations():
    origin = Location.objects.create(
        name="Москва",
        latitude=Decimal("55.7558"),
        longitude=Decimal("37.6173"),
    )
    destination = Location.objects.create(
        name="Подольск",
        latitude=Decimal("55.4312"),
        longitude=Decimal("37.5447"),
    )
    return origin, destination


def create_trip(manager, transport, locations, cargo_name="Архивный груз"):
    origin, destination = locations
    order = ShipmentOrder.objects.create(
        manager=manager,
        transport=transport,
        cargo_name=cargo_name,
        cargo_type="Паллеты",
        cargo_weight_kg=Decimal("1000.00"),
        desired_delivery_date="2026-06-01",
    )
    OrderPoint.objects.create(
        order=order,
        location=origin,
        sequence=1,
        point_type=OrderPoint.PointType.PICKUP,
    )
    OrderPoint.objects.create(
        order=order,
        location=destination,
        sequence=2,
        point_type=OrderPoint.PointType.DELIVERY,
    )
    RouteCalculationService().calculate_for_order(order)
    return TripLifecycleService().approve_route(order, order.route_options.first(), manager)


def deliver_trip(trip, manager):
    finished_at = timezone.make_aware(datetime(2026, 6, 12, 12, 0))
    service = TripLifecycleService()
    service.start_trip(trip, manager, actual_start_at=finished_at - timedelta(hours=2))
    service.deliver_trip(trip, manager, actual_finish_at=finished_at)
    trip.refresh_from_db()
    return trip


def save_test_document(
    owner,
    *,
    title="Архивный документ",
    file_format="pdf",
    content=b"%PDF-test",
):
    return DocumentArchiveService().save_document(
        content_bytes=content,
        document_type=ArchivedDocument.DocumentType.WAYBILL_PDF,
        file_format=file_format,
        title=title,
        owner=owner,
        created_by=owner,
        metadata={"source": "test"},
    )


@pytest.mark.django_db
def test_archive_service_stores_file_with_local_storage(manager, settings):
    document = save_test_document(manager, content=b"%PDF-local-archive")

    assert document.file_size_bytes == len(b"%PDF-local-archive")
    assert document.metadata_json == {"source": "test"}
    assert document.file.name.startswith("document_archive/")
    assert (settings.MEDIA_ROOT / document.file.name).exists()


@pytest.mark.django_db
def test_archive_list_scope_for_manager_and_admin(client, manager, other_manager, admin_user):
    own_document = save_test_document(manager, title="Свой документ")
    other_document = save_test_document(other_manager, title="Чужой документ")
    company_document = DocumentArchiveService().save_document(
        content_bytes=b"PK-company",
        document_type=ArchivedDocument.DocumentType.ADMIN_ANALYTICS_XLSX,
        file_format=ArchivedDocument.FileFormat.XLSX,
        title="Сводка компании",
        created_by=admin_user,
    )

    response = client.get(reverse("reports:archive"))
    assert response.status_code == 302

    client.force_login(manager)
    response = client.get(reverse("reports:archive"))
    content = response.content.decode()
    assert response.status_code == 200
    assert own_document.title in content
    assert other_document.title not in content
    assert company_document.title not in content

    client.force_login(admin_user)
    response = client.get(reverse("reports:archive"))
    content = response.content.decode()
    assert response.status_code == 200
    assert own_document.title in content
    assert other_document.title in content
    assert company_document.title in content


@pytest.mark.django_db
def test_archive_download_permissions_and_response(client, manager, other_manager, admin_user):
    own_document = save_test_document(manager, content=b"%PDF-own")
    other_document = save_test_document(other_manager, content=b"%PDF-other")

    response = client.get(reverse("reports:archive_download", kwargs={"pk": own_document.pk}))
    assert response.status_code == 302

    client.force_login(manager)
    response = client.get(reverse("reports:archive_download", kwargs={"pk": other_document.pk}))
    assert response.status_code == 404

    response = client.get(reverse("reports:archive_download", kwargs={"pk": own_document.pk}))
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert "attachment;" in response["Content-Disposition"]
    assert b"".join(response.streaming_content) == b"%PDF-own"

    client.force_login(admin_user)
    response = client.get(reverse("reports:archive_download", kwargs={"pk": other_document.pk}))
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert b"".join(response.streaming_content) == b"%PDF-other"


@pytest.mark.django_db
def test_archive_page_contains_delete_button(client, manager):
    document = save_test_document(manager, title="Документ для удаления")
    client.force_login(manager)

    response = client.get(reverse("reports:archive"))
    content = response.content.decode()

    assert response.status_code == 200
    assert reverse("reports:archive_delete", kwargs={"pk": document.pk}) in content
    assert "Удалить" in content


@pytest.mark.django_db
def test_manager_deletes_own_archive_document_and_file(client, manager, settings):
    document = save_test_document(manager, content=b"%PDF-delete-me")
    file_path = settings.MEDIA_ROOT / document.file.name
    assert file_path.exists()
    client.force_login(manager)

    response = client.post(reverse("reports:archive_delete", kwargs={"pk": document.pk}))

    assert response.status_code == 302
    assert not ArchivedDocument.objects.filter(pk=document.pk).exists()
    assert not file_path.exists()


@pytest.mark.django_db
def test_manager_cannot_delete_other_manager_document(client, manager, other_manager, settings):
    document = save_test_document(other_manager, content=b"%PDF-keep-me")
    file_path = settings.MEDIA_ROOT / document.file.name
    assert file_path.exists()
    client.force_login(manager)

    response = client.post(reverse("reports:archive_delete", kwargs={"pk": document.pk}))

    assert response.status_code == 404
    assert ArchivedDocument.objects.filter(pk=document.pk).exists()
    assert file_path.exists()


@pytest.mark.django_db
def test_admin_deletes_any_archive_document_and_file(client, other_manager, admin_user, settings):
    document = save_test_document(other_manager, content=b"%PDF-admin-delete")
    file_path = settings.MEDIA_ROOT / document.file.name
    assert file_path.exists()
    client.force_login(admin_user)

    response = client.post(reverse("reports:archive_delete", kwargs={"pk": document.pk}))

    assert response.status_code == 302
    assert not ArchivedDocument.objects.filter(pk=document.pk).exists()
    assert not file_path.exists()


@pytest.mark.django_db
def test_anonymous_user_cannot_delete_archive_document(client, manager, settings):
    document = save_test_document(manager, content=b"%PDF-anonymous-keep")
    file_path = settings.MEDIA_ROOT / document.file.name

    response = client.post(reverse("reports:archive_delete", kwargs={"pk": document.pk}))

    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:login"))
    assert ArchivedDocument.objects.filter(pk=document.pk).exists()
    assert file_path.exists()


@pytest.mark.django_db
def test_deleting_archived_waybill_keeps_trip_order_and_direct_pdf_fields(
    client, manager, transport, locations, settings
):
    trip = deliver_trip(create_trip(manager, transport, locations), manager)
    document = DocumentArchiveService().save_document(
        content_bytes=b"%PDF-waybill-archive",
        document_type=ArchivedDocument.DocumentType.WAYBILL_PDF,
        file_format=ArchivedDocument.FileFormat.PDF,
        title=f"Путевой лист рейса №{trip.pk}",
        owner=manager,
        created_by=manager,
        related_order=trip.order,
        related_trip=trip,
    )
    file_path = settings.MEDIA_ROOT / document.file.name
    order_pk = trip.order.pk
    client.force_login(manager)

    response = client.post(reverse("reports:archive_delete", kwargs={"pk": document.pk}))

    assert response.status_code == 302
    assert not ArchivedDocument.objects.filter(pk=document.pk).exists()
    assert not file_path.exists()
    trip.refresh_from_db()
    assert Trip.objects.filter(pk=trip.pk).exists()
    assert ShipmentOrder.objects.filter(pk=order_pk).exists()
    assert not trip.waybill_pdf


@pytest.mark.django_db
def test_direct_downloads_do_not_create_archive_records(
    client, manager, transport, locations
):
    trip = deliver_trip(create_trip(manager, transport, locations), manager)
    client.force_login(manager)

    assert client.get(reverse("reports:emissions_pdf")).status_code == 200
    assert client.get(reverse("reports:emissions_xlsx")).status_code == 200
    assert client.get(reverse("trips:export_xlsx")).status_code == 200
    assert client.get(reverse("trips:waybill", kwargs={"pk": trip.pk})).status_code == 200
    assert ArchivedDocument.objects.count() == 0


@pytest.mark.django_db
def test_manager_archive_save_actions_create_documents(client, manager, transport, locations):
    trip = deliver_trip(create_trip(manager, transport, locations), manager)
    client.force_login(manager)

    response = client.post(
        reverse("reports:emissions_pdf_archive"),
        {"date_from": "2026-06-01", "date_to": "2026-06-30"},
    )
    assert response.status_code == 302
    response = client.post(reverse("reports:emissions_xlsx_archive"))
    assert response.status_code == 302
    response = client.post(reverse("trips:export_xlsx_archive"), {"status": Trip.Status.DELIVERED})
    assert response.status_code == 302
    response = client.post(reverse("trips:waybill_archive", kwargs={"pk": trip.pk}))
    assert response.status_code == 302

    documents = ArchivedDocument.objects.order_by("document_type")
    assert {document.document_type for document in documents} == {
        ArchivedDocument.DocumentType.EMISSIONS_PDF,
        ArchivedDocument.DocumentType.EMISSIONS_XLSX,
        ArchivedDocument.DocumentType.TRIPS_XLSX,
        ArchivedDocument.DocumentType.WAYBILL_PDF,
    }
    assert all(document.owner == manager for document in documents)
    waybill_document = documents.get(document_type=ArchivedDocument.DocumentType.WAYBILL_PDF)
    assert waybill_document.related_trip == trip
    trips_document = documents.get(document_type=ArchivedDocument.DocumentType.TRIPS_XLSX)
    assert trips_document.metadata_json["status"] == Trip.Status.DELIVERED
    assert trips_document.metadata_json["trips_count"] == 1


@pytest.mark.django_db
def test_admin_dashboard_archive_save_action(client, admin_user):
    client.force_login(admin_user)

    response = client.post(reverse("dashboard:admin_dashboard_xlsx_archive"))

    assert response.status_code == 302
    document = ArchivedDocument.objects.get()
    assert document.document_type == ArchivedDocument.DocumentType.ADMIN_ANALYTICS_XLSX
    assert document.file_format == ArchivedDocument.FileFormat.XLSX
    assert document.owner is None
    assert document.created_by == admin_user
    assert document.file_size_bytes > 0
    assert document.metadata_json["source"] == "admin_dashboard"


@pytest.mark.django_db
def test_xlsx_archive_download_content_type(client, manager):
    document = save_test_document(
        manager,
        title="Excel документ",
        file_format=ArchivedDocument.FileFormat.XLSX,
        content=b"PK-xlsx",
    )
    client.force_login(manager)

    response = client.get(reverse("reports:archive_download", kwargs={"pk": document.pk}))

    assert response.status_code == 200
    assert response["Content-Type"] == XLSX_CONTENT_TYPE
    assert "attachment;" in response["Content-Disposition"]
    assert b"".join(response.streaming_content) == b"PK-xlsx"


@pytest.mark.django_db
def test_use_s3_storage_false_does_not_require_minio(client, manager):
    client.force_login(manager)

    response = client.post(reverse("trips:export_xlsx_archive"), {"status": Trip.Status.DELIVERED})

    assert response.status_code == 302
    document = ArchivedDocument.objects.get()
    assert document.file.name.startswith("document_archive/")
