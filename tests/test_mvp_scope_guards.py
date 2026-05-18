from pathlib import Path

import pytest
from django.urls import reverse


def test_no_new_dependencies_added_for_phase_8():
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
        "pytest",
        "pytest-django",
        "ruff",
    }


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


@pytest.mark.django_db
def test_no_excel_endpoint_exists_after_phase_7(client):
    assert client.get("/reports/emissions.xlsx/").status_code == 404
    assert client.get("/analytics.xlsx/").status_code == 404
    assert reverse("dashboard:manager_analytics") == "/analytics/"
