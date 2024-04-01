import pytest
from django.db import transaction, IntegrityError
from django.test import TestCase
from django.core.management import call_command
from status.models import Status
from status.models import Service

pytestmark = pytest.mark.django_db


class TestCommands(TestCase):

    def test_create_initial_objects_creates_five_objects (self):
        call_command('create_initial_objects')
        assert Status.objects.count() == 5


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

