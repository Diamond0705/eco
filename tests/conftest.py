import os

import pytest

os.environ["ROUTE_PROVIDER"] = "mock"
os.environ["GRAPHHOPPER_API_KEY"] = ""


@pytest.fixture(autouse=True)
def default_mock_route_provider(settings):
    settings.ROUTE_PROVIDER = "mock"
    settings.GRAPHHOPPER_API_KEY = ""
