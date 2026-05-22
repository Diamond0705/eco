import subprocess
import sys
from pathlib import Path

import pytest
from django.urls import reverse


def test_only_approved_dependencies_are_used():
    requirements = {
        line.strip()
        for line in Path("requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }

    assert requirements == {
        "Django>=5.2.8,<5.3",
        "psycopg[binary]",
        "django-environ",
        "reportlab",
        "openpyxl>=3.1,<4",
        "django-storages[s3]>=1.14,<2",
        "waitress>=3,<4",
        "pytest",
        "pytest-django",
        "ruff",
    }
    # openpyxl is the only approved Phase 16 reporting dependency: it writes .xlsx exports
    # without bringing in heavier analytics stacks.
    # django-storages[s3] is the only approved Phase 17 storage dependency: it connects
    # the private document archive to MinIO/S3-compatible storage.
    # waitress is the approved Phase 18 WSGI server for Windows-friendly deployment.
    assert "pandas" not in requirements
    assert "numpy" not in requirements
    assert "gunicorn" not in requirements


def test_graphhopper_added_without_forbidden_external_http_dependencies():
    source_paths = [
        path
        for directory in ("apps", "config")
        for path in Path(directory).rglob("*.py")
        if ".venv" not in path.parts
    ]
    combined_source = "\n".join(path.read_text(encoding="utf-8") for path in source_paths)

    assert "GraphHopperRouteProvider" in combined_source
    assert "requests." not in combined_source
    assert "httpx." not in combined_source
    assert "aiohttp" not in combined_source
    assert "celery" not in combined_source.lower()
    assert "rest_framework" not in combined_source
    assert "jwt" not in combined_source.lower()
    assert "postgis" not in combined_source.lower()
    assert "redis" not in combined_source.lower()
    assert "gunicorn" not in combined_source.lower()


@pytest.mark.django_db
def test_legacy_excel_endpoints_stay_absent(client):
    assert client.get("/reports/emissions.xlsx/").status_code == 404
    assert client.get("/analytics.xlsx/").status_code == 404
    assert reverse("dashboard:manager_analytics") == "/analytics/"


def test_no_pending_model_migrations():
    result = subprocess.run(
        [sys.executable, "manage.py", "makemigrations", "--check", "--dry-run"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
