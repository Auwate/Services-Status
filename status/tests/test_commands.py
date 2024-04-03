from django.test import TestCase
from django.core.management import call_command
from status.models import Status


class TestCommands(TestCase):

    def test_create_initial_objects_creates_five_objects (self):
        call_command('create_initial_objects')
        assert Status.objects.count() == 5