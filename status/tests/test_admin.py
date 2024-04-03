from django.test import TestCase
from django.utils import timezone
from status.models import Ticket, SubService, Service, ClientDomain, Status
from status.admin import TicketAdmin
from django.contrib.admin.sites import AdminSite
import datetime


class TestAdmin(TestCase):

    def test_order_by_of_tickets_in_admin (self):
        '''
        Checks the ordering of Ticket objects in the admin panel.
        Currently, it should be sorted based on the recency of the "begin" field.
        '''
        # Create required fields
        sub_serv = SubService.objects.create(name='Test_Sub', subservice_description='')
        serv = Service.objects.create(name='Test_Service', service_description='', scope='Inter-Domain')
        stat = Status.objects.create(tag= "Alert", color_name = "Orange", color_hex = "#FC810D", class_design = "fas fa-exclamation-circle")
        client = ClientDomain.objects.create(name='Test_Client', domain_description='')
        client.services.set([serv])

        # Create ticket that started right now
        ticket = Ticket.objects.create(status=stat, begin=timezone.now(), end=timezone.now(), notify_action=False)
        ticket.sub_service.set([sub_serv])
        ticket.services.set([serv])
        ticket.client_domains.set([client])
        
        # Create a ticket that started an hour ago
        ticket2 = Ticket.objects.create(status=stat, begin=timezone.now() + datetime.timedelta(hours=-1), end=timezone.now(), notify_action=False)
        ticket2.sub_service.set([sub_serv])
        ticket2.services.set([serv])
        ticket2.client_domains.set([client])

        # Create a ticket that started two hours ago
        ticket3 = Ticket.objects.create(status=stat, begin=timezone.now() + datetime.timedelta(hours=-2), end=timezone.now(), notify_action=False)
        ticket3.sub_service.set([sub_serv])
        ticket3.services.set([serv])
        ticket3.client_domains.set([client])
        
        admin_site = AdminSite()
        ticket_admin = TicketAdmin(Ticket, admin_site)

        query_set = ticket_admin.get_queryset(None)
        query_set = [str(element) for element in query_set]

        self.assertEqual(query_set, ['T000000001', 'T00000002', 'T00000003'])
        