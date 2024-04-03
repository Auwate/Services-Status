# -*- coding: utf-8 -*-
"""
This module will define all the models and their
relationships to build up the Application logic.
"""
from datetime import datetime

import pytz
from ckeditor.fields import RichTextField
from colorfield.fields import ColorField
from django.db import models
from django.utils.html import format_html
from django.utils.text import Truncator
from django.utils.translation import ugettext_lazy as _


class Service(models.Model):
    """
    Class to specify the Services model.
        - A Service name and description define its structure.
        - The Service name will be mandatory, but no the description field.
        - The name field could have a maximum of 100 characters.
        - The description field will store an HTML enriched text content.
        - The scope field will identify if service is inter-domain or multi-domain
    """
    MULTI_DOMAIN = "multi_domain"
    INTER_DOMAIN = "inter_domain"
    DOMAIN_CHOICES = (
        (MULTI_DOMAIN, "Multi-Domain"),
        (INTER_DOMAIN, "Inter-Domain")
    )

    name = models.CharField(unique=True, max_length=100, verbose_name='Service')
    service_description = RichTextField(blank=True, null=True, verbose_name='Description')
    scope = models.CharField(max_length=30, choices=DOMAIN_CHOICES, default=MULTI_DOMAIN, blank=False)

    def description(self):
        """
        Method to truncate and render HTML content.
            - This action will allow visualizing a short
            description during the object listing process.
            - The HTML render process will help to visualize
            HTML rendered content on the listed object's stories.
        :return: a truncated value formatted to HTML
        """
        if self.service_description is not None:
            return format_html(Truncator(self.service_description).chars(250))
        return self.service_description

    description.allow_tags = True

    class Meta:
        verbose_name = _("Service")
        verbose_name_plural = _("Services")
        ordering = ['name']

    def __str__(self):
        return self.name

    def scope_type(self):
        return str(self.scope).upper()


class ClientDomain(models.Model):
    """
    Class to specify the Client Domain model.
        - A Client Domain name, a description, and a relationship
        to the Service module define its structure.
        - The Client Domain name will be mandatory, but no the description field.
        - The name field could have a maximum of 100 characters.
        - The description field will store an HTML enriched text content.
        - The relationship with Services will help to set a
        client domain to many services and vice versa.
    """
    name = models.CharField(unique=True, max_length=100, verbose_name='Client Domain')
    domain_description = RichTextField(blank=True, null=True, verbose_name='Description')
    services = models.ManyToManyField(Service)

    def description(self):
        """
        Method to render HTML content.
            - This action will allow visualizing a short
            description during the object listing process.
            - The HTML render process will help to visualize
            HTML rendered content on the listed object's stories.
        :return: No return
        """
        if self.domain_description is not None:
            return format_html(self.domain_description)
        return self.domain_description

    description.allow_tags = True

    class Meta:
        verbose_name = _("Client Domain")
        verbose_name_plural = _("Client Domains")
        ordering = ['name']

    def __str__(self):
        return self.name


class Region(models.Model):
    """
    Class to specify the Region Model/Table
        - A Region name, a description, and a relationship
        to the ClientDomain module define its structure.
        - The Region name will be mandatory, but no the description field.
        - The name field could have a maximum of 100 characters.
        - The description field will store an HTML enriched text content.
        - The relationship with ClientDomain will help to set a
        region to many client domains and vice versa.
    """

    name = models.CharField(unique=True, max_length=100, verbose_name='Region')
    region_description = RichTextField(blank=True, null=True, verbose_name='Description')
    client_domains = models.ManyToManyField(ClientDomain)

    def description(self):
        """
        Method to support HTML formatting.
        This will allow to visualize HTML enriched description
        on the administrator zone related to the email domains.
        :return: A html formatted description
        """
        if self.region_description is not None:
            return format_html(self.region_description)
        return self.region_description

    description.allow_tags = True

    class Meta:
        verbose_name = _("Region")
        verbose_name_plural = _("Regions")
        ordering = ['name']

    def __str__(self):
        return self.name


class SubService(models.Model):
    """
    Class to specify the Subservices Model/Table
        - A SubService name, a description define its structure.
        - The Subservice name will be mandatory, but no the description field.
        - The name field could have a maximum of 100 characters.
        - The description field will store an HTML enriched text content.
    """

    name = models.CharField(unique=True, max_length=100, verbose_name='Sub-Service')
    subservice_description = RichTextField(blank=True, null=True, verbose_name='Description')

    def description(self):
        """
        Method to support HTML formatting.
        This will allow to visualize HTML enriched description
        on the administrator zone related to the email domains.
        :return: A html formatted description
        """
        if self.subservice_description is not None:
            return format_html(self.subservice_description)
        return self.subservice_description

    description.allow_tags = True

    class Meta:
        verbose_name = _("Sub-Service")
        verbose_name_plural = _("Sub-Services")
        ordering = ['name']

    def __str__(self):
        return self.name


class Priority(models.Model):
    """
    Class to specify the Priority Model/Table
        - A priority tag, a color, and a hexadecimal color value define its structure.
        - All of them will be mandatory.
    """

    tag = models.CharField(unique=True, max_length=25)
    color = models.CharField(unique=True, max_length=7)
    color_hex = ColorField(unique=True, default='#000000')

    class Meta:
        verbose_name = _("Priority")
        verbose_name_plural = _("Priorities")
        ordering = ['tag']

    def __str__(self):
        return self.tag


class Topology(models.Model):
    """
    Class to specify the Topology Model/Table
        - A relationship to services, a relationship to subservices, and a relationship
        to the priority module define its structure.
        - The relationship with Subservices will help to set a
        topology to many subservices and vice versa under different services.
    """

    service = models.ForeignKey(Service, models.CASCADE, verbose_name='Service')
    subservices = models.ManyToManyField(SubService, verbose_name='Sub - Service')
    priority = models.ForeignKey(Priority, models.DO_NOTHING)

    class Meta:
        verbose_name = _("Topology")
        verbose_name_plural = _("Topologies")

    def subservices_list(self):
        """
        Method to create an HTML enriched list
        :return:
        """
        return format_html("<br>".join([subservice.name for subservice in self.subservices.all()]))

    subservices_list.allow_tags = True

    def __str__(self):
        return "Topology {0}: about Service {1}, {2} " \
               "priority".format(self.pk, self.service, self.priority)


class Status(models.Model):
    """
    Class to specify the Status Model/Table
        - A tag name, a color name, a hexadecimal color value,
        and a class design definition define its structure.
    """

    tag = models.CharField(unique=True, max_length=45, verbose_name='Status')
    color_name = models.CharField(unique=True, max_length=7)
    color_hex = ColorField(default='#000000')
    class_design = models.CharField(unique=True, max_length=50)
    visual_order = models.IntegerField(blank=True, default=1)

    class Meta:
        verbose_name = _("Status Category")
        verbose_name_plural = _("Status Categories")

    def __str__(self):
        return self.tag


def get_new_ticket_id():
    # this method returns the 'id' of the last ticket object added to the DB and increments it by 1
    # if 8 ticket objects are in the database it will return T000000009
    latest_tickets_id_plus1 = 'T000000001'
    if Ticket.objects.values().count() > 0:
        latest_tickets_id_plus1 = 'T' + str(Ticket.objects.values().latest('id')['id'] + 1).zfill(8)
    return latest_tickets_id_plus1


class Ticket(models.Model):
    """
    Class to specify the Ticket Model/Table
        - A Ticket ID value, a relationship to Subservice Module,
        a begin - end dates, actions (descriptions and notes),
        and a notification field define its structure.
        - The Client Domain name will be mandatory, but no the description field.
        - The name field could have a maximum of 100 characters.
        - The actions (notes and description) fields will store an HTML enriched text content.
        - The relationship with SubServices will help to relate a
        ticket to a subservice.
        - The notification action field will control the notification process
    """

    NO = False
    YES = True
    YES_NO_CHOICES = (
        (NO, 'No'),
        (YES, 'Yes')
    )

    ticket_id = models.CharField(unique=True, max_length=10, default=get_new_ticket_id)

    # sub-service to sub-services
    sub_service = models.ManyToManyField(SubService, blank=True, verbose_name='Sub - Services')
    services = models.ManyToManyField(Service, blank=True, verbose_name='Service')
    client_domains = models.ManyToManyField(ClientDomain, blank=True, verbose_name='Client Domains')

    # This action (models.SET_NULL) will allow keeping tickets regardless of
    # the deletion of the sub-service where they belong.
    # sub_service = models.ForeignKey(SubService, models.SET_NULL,
    #                                 null=True, verbose_name='Sub-Service')

    status = models.ForeignKey(Status, models.DO_NOTHING,
                               null=True, default=3, verbose_name='Status')
    begin = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
        
    # UTC-5 is standard for Miami, but drop-down with list is appropriate

    action_description = RichTextField()
    action_notes = RichTextField(blank=True, null=True)

    notify_action = models.BooleanField(
        default=YES,
        choices=YES_NO_CHOICES,
        verbose_name='Ticket notified')

    def subservices_list(self):
        """
        Method to create an HTML enriched list
        :return:
        """
        return format_html("<br>".join([sub_service.name for sub_service in self.sub_service.all()]))

    subservices_list.allow_tags = True

    class Meta:
        verbose_name = _("Ticket")
        verbose_name_plural = _("Tickets")

    @property
    def is_in_process(self):
        localized_current_time = datetime.now(pytz.utc)
        return localized_current_time > self.begin

    def __str__(self):
        # return "{0} in {1}".format(self.service_category, self.business_service)
        return self.ticket_id


class TicketLog(models.Model):
    """
    Class to specify the TicketLog Model/Table
        - A ticket relationship, an status relationship,
        and actions (dates and notes) define its structure.
        - The action notes field will store an HTML enriched text content.
        - The relationship with Ticket will help to related a
        log to a certain ticket.
    """

    ticket = models.ForeignKey(Ticket, models.CASCADE)
    status = models.ForeignKey(Status, models.DO_NOTHING)
    action_date = models.DateTimeField()
    action_notes = RichTextField(blank=True, null=True, verbose_name='Notes')

    def description (self):
        if self.action_notes is not None:
            return format_html(self.action_notes)
        return self.action_notes

    description.allow_tags = True

    def __str__(self):
        queryset_list = []
        for sub_service in self.ticket.sub_service.all():
            queryset_list.append(sub_service.name)
        
        # adjust ticket log for subservices
        return "{0} in Ticket: {1}".format("---".join(queryset_list), self.ticket.ticket_id)


class Subscriber(models.Model):
    """
    Class to specify the Subscriber Model/Table
        - A Subscriber name, a email, a token, and a relationship
        to the Service and the Subservice modules define its structure.
        - The relationship with Services will help to set a
        subscriber to many services and vice versa, the same with subservice.
    """

    name = models.CharField(max_length=45)
    email = models.CharField(max_length=45)
    token = models.CharField(max_length=128, null=True, blank=True)
    services = models.ManyToManyField(Service, verbose_name='Service', blank=True)
    subservices = models.ManyToManyField(SubService, verbose_name='Sub - Service', blank=True)

    class Meta:
        verbose_name = _("Subscriber")
        verbose_name_plural = _("Subscribers")

    def __str__(self):
        return self.name


class EmailDomain(models.Model):
    """
    Class to specify the EmailDomain Model/Table
        - A Email Domain name, and a description, define its structure.
        - The Email Domain name will be mandatory, but no the description field.
        - The name field could have a maximum of 100 characters.
        - The description field will store an HTML enriched text content.
    """

    domain = models.CharField(unique=True, max_length=100, verbose_name='Domain Name')
    domain_description = RichTextField(blank=True, null=True, verbose_name='Description')

    def description(self):
        """
        Method to support HTML formatting.
        This will allow to visualize HTML enriched description
        on the administrator zone related to the email domains.
        :return: A html formatted description
        """
        if self.domain_description is not None:
            return format_html(self.domain_description)
        return self.domain_description

    description.allow_tags = True

    class Meta:
        verbose_name = _("Email Domain")
        verbose_name_plural = _("Email Domains")

    def __str__(self):
        return self.domain
