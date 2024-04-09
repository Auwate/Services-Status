from status.models import Service, SubService, Status, ClientDomain, Ticket
from django.utils import timezone
from django.urls import reverse
from django.test import TestCase

class TestTickets(TestCase):

    def test_ticket_latest_action_notes_and_date_exist (self):

        # Create all the status objects
        initial_objects = [
            {"tag":"Alert", "color_name": "Orange", "color_hex":"#FC810D", "class_design": "fas fa-exclamation-circle"},
            {"tag":"In Process", "color_name": "Yellow", "color_hex":"#DBBF07", "class_design": "fas fa-tools"},
            {"tag":"No Issues", "color_name": "Green", "color_hex":"#0AC739", "class_design": "fas fa-check-circle"},
            {"tag":"Outage", "color_name": "Red", "color_hex":"#F00004", "class_design": "fas fa-times-circle"},
            {"tag":"Planned", "color_name": "Blue", "color_hex":"#041DBF", "class_design": "far fa-calendar-alt"}
        ]
                
        for data_objects in initial_objects:
            Status.objects.create(**data_objects)

        # Create the required fields
        sub_serv = SubService.objects.create(name='Test_Sub', subservice_description='')
        serv = Service.objects.create(name='Test_Service', service_description='', scope='Inter-Domain')
        stat = Status.objects.get(tag="No Issues")
        client = ClientDomain.objects.create(name='Test_Client', domain_description='')
        client.services.set([serv])

        # Create Ticket object
        ticket = Ticket.objects.create(status=stat, begin=timezone.now(), end=timezone.now(), notify_action=False)
        ticket.sub_service.set([sub_serv])
        ticket.services.set([serv])
        ticket.client_domains.set([client])

        # Get the url to the main page. Reverse does this by using the name field in urls.py
        url = reverse('services_status_view') 

        # Get the response
        response = self.client.get(url)

        # Make sure it returns a 200 response, this checks if an error has occurred generally
        self.assertEqual(response.status_code, 200)

        # Get the queryset for the ticket_list
        queryset = response.context['ticket_list']

        # Make sure the attribute exists
        for element in queryset:
            self.assertTrue(hasattr(element, "latest_action_notes"))
            self.assertTrue(hasattr(element, "latest_action_date"))
