from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.locations.models import Location


@pytest.mark.django_db
def test_location_creation():
    location = Location.objects.create(
        name="Москва",
        address="Москва",
        latitude=Decimal("55.7558"),
        longitude=Decimal("37.6173"),
    )

    assert str(location) == "Москва"
    assert location.latitude == Decimal("55.7558")
    assert location.longitude == Decimal("37.6173")
    assert location.is_active is True


@pytest.mark.django_db
def test_location_coordinate_validation():
    location = Location(
        name="Некорректная точка",
        latitude=Decimal("91.0000"),
        longitude=Decimal("181.0000"),
    )

    with pytest.raises(ValidationError):
        location.full_clean()
