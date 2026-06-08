import os
import subprocess
import sys

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

import config.settings as project_settings
from apps.reports.models import ArchivedDocument
from apps.reports.services.document_archive import DocumentArchiveService

User = get_user_model()


@pytest.fixture
def manager():
    return User.objects.create_user(
        username="security_deploy_manager",
        password="StrongPass12345",
        role=User.Role.MANAGER,
    )


@pytest.fixture(autouse=True)
def local_archive_storage(settings, tmp_path):
    settings.USE_S3_STORAGE = False
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.MEDIA_URL = "/media/"


def test_healthcheck_endpoint_returns_ok(client):
    response = client.get("/healthz/")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/plain")
    assert response.content == b"ok"


def test_local_default_security_settings_keep_http_dev_workflow():
    assert project_settings.DEBUG is True
    assert project_settings.SESSION_COOKIE_HTTPONLY is True
    assert project_settings.SESSION_COOKIE_SECURE is False
    assert project_settings.CSRF_COOKIE_SECURE is False
    assert project_settings.SECURE_SSL_REDIRECT is False
    assert project_settings.SECURE_HSTS_SECONDS == 0
    assert project_settings.SECURE_CONTENT_TYPE_NOSNIFF is True
    assert project_settings.X_FRAME_OPTIONS == "DENY"
    assert not hasattr(project_settings, "SECURE_PROXY_SSL_HEADER")


def test_allowed_hosts_and_csrf_trusted_origins_are_env_driven():
    env = {
        **os.environ,
        "DEBUG": "False",
        "SECRET_KEY": "phase-18-production-secret",
        "ALLOWED_HOSTS": "ecologist.example.com,localhost",
        "CSRF_TRUSTED_ORIGINS": "https://ecologist.example.com,https://www.example.com",
        "USE_X_FORWARDED_PROTO": "True",
    }
    script = (
        "import config.settings as s; "
        "print('|'.join(s.ALLOWED_HOSTS)); "
        "print('|'.join(s.CSRF_TRUSTED_ORIGINS)); "
        "print(s.SECURE_PROXY_SSL_HEADER)"
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "ecologist.example.com|localhost" in result.stdout
    assert "https://ecologist.example.com|https://www.example.com" in result.stdout
    assert "('HTTP_X_FORWARDED_PROTO', 'https')" in result.stdout


def test_blank_allowed_hosts_and_csrf_trusted_origins_are_safe():
    env = {
        **os.environ,
        "ALLOWED_HOSTS": "",
        "CSRF_TRUSTED_ORIGINS": "",
    }
    script = (
        "import config.settings as s; "
        "print('|'.join(s.ALLOWED_HOSTS)); "
        "print(s.CSRF_TRUSTED_ORIGINS)"
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "127.0.0.1|localhost" in result.stdout
    assert "[]" in result.stdout


def test_deploy_compose_publishes_minio_ports_for_local_verification():
    compose = open("docker-compose.deploy.yml", encoding="utf-8").read()

    assert 'AWS_S3_ENDPOINT_URL: http://minio:9000' in compose
    assert '      - "9000:9000"' in compose
    assert '      - "9001:9001"' in compose
    assert "Published for local Phase 18 verification only." in compose


def test_deploy_dockerfile_installs_cyrillic_pdf_font():
    dockerfile = open("Dockerfile", encoding="utf-8").read()

    assert "apt-get install -y --no-install-recommends fonts-dejavu-core" in dockerfile
    assert "rm -rf /var/lib/apt/lists/*" in dockerfile


def test_deploy_entrypoint_applies_migrations_and_refreshes_staticfiles():
    entrypoint = open("docker/entrypoint.sh", encoding="utf-8").read()

    assert "python manage.py migrate --noinput" in entrypoint
    assert "python manage.py collectstatic --noinput --clear" in entrypoint


def test_debug_false_rejects_unsafe_secret_key():
    env = {
        **os.environ,
        "DEBUG": "False",
        "SECRET_KEY": "unsafe-local-dev-key",
    }

    result = subprocess.run(
        [sys.executable, "-c", "import config.settings"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "SECRET_KEY must be set to a production value" in result.stderr


@pytest.mark.django_db
def test_archive_downloads_remain_protected(client, manager):
    document = DocumentArchiveService().save_document(
        content_bytes=b"%PDF-protected",
        document_type=ArchivedDocument.DocumentType.WAYBILL_PDF,
        file_format=ArchivedDocument.FileFormat.PDF,
        title="Protected archive document",
        owner=manager,
        created_by=manager,
    )

    response = client.get(reverse("reports:archive_download", kwargs={"pk": document.pk}))

    assert response.status_code == 302
    assert response["Location"].startswith(reverse("accounts:login"))
