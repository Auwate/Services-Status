import pytest
from django.db import transaction, IntegrityError

from status.models import Service

pytestmark = pytest.mark.django_db


class TestService(object):

    @pytest.mark.django_db
    def test_service_creation(self):

        Service.objects.create(name="Service test")
        assert Service.objects.count() == 1

    @pytest.mark.django_db
    def test_service_integrity(self):

        Service.objects.create(name="Service test")

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Service.objects.create(name="Service test")

        assert Service.objects.count() == 1

