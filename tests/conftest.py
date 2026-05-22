import os

import pytest

os.environ["ROUTE_PROVIDER"] = "mock"
os.environ["CALCULATION_MODEL"] = "v2.1"
os.environ["GRAPHHOPPER_API_KEY"] = ""
os.environ["USE_S3_STORAGE"] = "False"
os.environ["AWS_S3_ENDPOINT_URL"] = "http://localhost:9000"


@pytest.fixture(autouse=True)
def default_mock_route_provider(settings):
    settings.ROUTE_PROVIDER = "mock"
    settings.CALCULATION_MODEL = "v2.1"
    settings.GRAPHHOPPER_API_KEY = ""
    settings.USE_S3_STORAGE = False
