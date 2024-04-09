import secrets
from datetime import timedelta
from distutils.util import strtobool
from itertools import chain

from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from .forms import SubscriberDataForm
from .forms import SubscriberForm
from .models import SubService, Ticket, Status, Service, TicketLog, Region, Subscriber, EmailDomain, ClientDomain


class ServicesStatusView(View):
    """
    Services Status Visualization page
    """

    template_name = "services_status.html"

    @staticmethod
    def remove_sessions(request):

        # Remove all the variable sessions related to this view
        if request.session.get('object', None) is not None:
            del request.session['object']

        if request.session.get('service_id', None) is not None:
            del request.session['service_id']

        if request.session.get('service_specific', None) is not None:
            del request.session['service_specific']

        if request.session.get('object_passed', None) is not None:
            del request.session['object_passed']

        if request.session.get('one_service', None) is not None:
            del request.session['one_service']

        if request.session.get('subs_updates', None) is not None:
            del request.session['subs_updates']

    def get(self, request, *args, **kwargs):

        global services

        today = timezone.now().date()
        self.remove_sessions(request)

        # Getting most recent 5 tickets
        # queryset = Ticket.objects.all().order_by('begin').reverse()[:5]
        # queryset = Ticket.objects.all().order_by('pk').reverse()[:5]

        # It will retrieve all the tickets lower than today - 4
        # (Last 5 days including today) based on the begin day information
        # queryset_down = Ticket.objects.filter(Q(begin__gte=(today - timedelta(4)))).order_by('pk').order_by('-pk')
        queryset_down = Ticket.objects.filter(Q(begin__gte=(today - timedelta(4))))

        # It will retrieve all the tickets grader than today
        # based on the end day information
        # queryset_up = Ticket.objects.filter(Q(end__gte=today)).order_by('pk').order_by('-pk')
        queryset_up = Ticket.objects.filter(Q(end__gte=today))

        # It will join query results precomputed before
        queryset = queryset_down.union(queryset_up)

        # Initializing queryset to empty
        recent_tickets = Ticket.objects.none()

        # new_queryset = None
        ticket_list = list()

        if queryset:
            recent_tickets_list = recent_tickets | queryset

            ticket_priorities = dict()
            for ticket in recent_tickets_list:
                status = ticket.status.tag

                if status not in ticket_priorities.keys():
                    ticket_priorities[status] = list()
                ticket_priorities[status].append(ticket)

            ticket_status = Status.objects.all().order_by('visual_order')
            for t_status in ticket_status:
                if t_status.tag in ticket_priorities.keys() and len(ticket_priorities[t_status.tag]):
                    custom_list = [ticket.id for ticket in ticket_priorities[t_status.tag]]
                    queryset = Ticket.objects.filter(pk__in=custom_list).order_by('-pk')

                    for in_ticket in queryset:
                        ticket_list.append(in_ticket)

            for ticket in ticket_list:
                last_log = TicketLog.objects.filter(ticket=ticket.id) \
                    .filter(action_date__range=["2012-01-01", timezone.now()]).order_by('action_date').last()
                if last_log is not None:
                    ticket.latest_log = last_log.status
                    ticket.latest_action_notes = last_log.description()
                    ticket.latest_action_date = last_log.action_date
                else:
                    ticket.latest_log = ticket.status
                    ticket.latest_action_notes = None
                    ticket.latest_action_date = None

        context = {
            "ticket_list": ticket_list,
            "service_active": True
        }

        # Getting list of status for legend
        status_list = Status.objects.all()
        context['status_list'] = status_list

        # Getting today's date
        today = timezone.now().date()
        list_of_five_days = [today]

        counter = 1
        while counter < 5:
            list_of_five_days.append(today - timedelta(days=counter))
            counter = counter + 1

        context['days'] = list_of_five_days

        # Getting list of regions
        regions = Region.objects.all()
        context['region_list'] = regions

        if 'regions_select' in request.GET:

            # Getting checked regions
            regions = request.GET.getlist('regions')

            # Getting list of services
            services = list()
            for region in regions:

                # Getting list of services
                queryset = Region.objects.filter(name=region)
                for e in queryset:
                    client_domain_services = e.client_domains.all().exclude(services__name=None). \
                        values('services__name')
                    services_list = client_domain_services.all().exclude(services__name=None). \
                        values_list('services__name', flat=True)
                    services = list(set(chain(services, services_list)))
                services.sort()
                context['services_list'] = services

            context['regions_checked'] = regions

        elif 'search_services' in request.GET:

            search_value = request.GET['search']
            services_list = list()
            for service in services:
                if search_value.lower() in service.name.lower():
                    services_list.append(service)

            if not services_list:
                context['no_search_results'] = True

            context['services_list'] = services_list
            context['search_value'] = search_value

        else:
            # Getting list of services
            services = list()
            services = list(dict.fromkeys(chain(services, Service.objects.all())))
            context['services_list'] = services

        # Declaring an empty dictionary to store status per day for each service
        service_status = dict()
        no_issues = Status.objects.filter(tag='No Issues')[0]

        # Getting list of tickets associated with each service
        for service in services:

            subservices = SubService.objects.filter(topology__service__name=service)

            # Initializing queryset to empty
            tickets_list = Ticket.objects.none()

            for subservice in subservices:
                queryset = Ticket.objects.filter(sub_service=subservice)
                if queryset:
                    tickets_list = tickets_list | queryset

            status_per_day = list()

            i = 0
            for day in list_of_five_days:
                open_tickets = tickets_list.filter(Q(begin__lte=(day + timedelta(days=1))) & Q(end__isnull=True))

                current_tickets = tickets_list.filter(begin__startswith=day)

                active_tickets_per_day = open_tickets.union(current_tickets).order_by('begin')

                status_per_day.append(i)
                status_per_day[i] = list()

                # if active_tickets_per_day:
                if active_tickets_per_day:
                    for ticket in active_tickets_per_day:
                        status_per_day[i].append({
                            ticket.id:
                                ticket.status})

                    if not status_per_day[i]:
                        status_per_day[i].append({'None': no_issues})

                else:
                    status_per_day[i].append({'None': no_issues})

                i = i + 1

            status_per_day.reverse()

            service_status[service] = status_per_day

        context['status'] = service_status

        return render(request, self.template_name, context)


class SubscriptionView(View):
    """
    Subscription page
    """

    template_name = "subscription.html"
    context = dict()

    def get(self, request, service_id=None, *args, **kwargs):
        """
        Method to:
        - update a process in case a user requested a
        subscription without selecting any services or sub-services
        - update a subscription given a service
        (coming from the service status history page and taking a service value by default)
        :param service_id:
        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        # Remove all the variable sessions related to this view
        # self.remove_sessions(request)

        # Getting values previously entered by user if any
        user_name = request.GET.get('user_name')
        user_email = request.GET.get('subscriber_email')

        # If the user did a registration attempt before show entered values
        if user_email:
            form = SubscriberDataForm(initial={'name': user_name, 'email': user_email})
        else:
            form = SubscriberDataForm()
            regions = Region.objects.all()

        # self.context = {"form": form, "subscription_active": True, 'subscribed': False}

        self.context = {"form": form, "regions": regions, "subscription_active": True, 'subscribed': False}

        # Apply regional filters to the Subscriptions
        if 'filter_region' in request.GET:

            # Maps values from the service table to values in the regions table in a dictionary.
            service_region_map = {
                'Cape Town': 'Africa',
                'Fortaleza': 'Brazil',
                'São Paulo': 'Brazil',
                'Panama City': 'Panama',
                'San Juan': 'Puerto Rico',
                'Santiago': 'Chile',
                'Miami': 'US',
                'Boca Raton': 'US',
                'USA': 'US'}

            # Get selected region from template
            selected_region = request.GET.get('filter_region')
            filtered_services = []

            # Add all services related to the region(by service_region_map dict) to the list: filtered_services
            # "US" requires a special case since it's a country tied to cities, instead of vice-versa.
            if selected_region == "US":
                for key, value in service_region_map.items():
                    if selected_region == value:
                        filtered_services.append(key)
            else:
                for key in service_region_map:
                    if selected_region == key:
                        filtered_services.append(service_region_map[key])

            # Pass list of services into filtering function
            form.filter_services(filtered_services)

        if service_id is not None:
            obj = get_object_or_404(Service, id=service_id)
            self.context['object'] = obj
            request.session['object'] = obj.name
            request.session['service_id'] = service_id

            self.context['service_specific'] = True

        else:
            if 'object' in request.GET:
                self.context['object_passed'] = request.GET.get('object')
                request.session['object_passed'] = request.GET.get('object')

            if 'service_specific' in request.GET:
                val = strtobool(request.GET.get('service_specific'))
                self.context['service_specific'] = bool(val)
            else:
                self.context['service_specific'] = False

            # If an update was requested but the user did not enter a valid email
            update_email = request.GET.get('email')

            self.context['update_email'] = update_email

        return render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):
        """
        Method to support the creation of a subscription.
        Here it will done all the verifications related to a new subscription
        1.0 - No service or sub-service selected
        2.0 - New subscriber, wrong email domain
        3.0 - Existing subscriber (existing email)
        3.1.- Existing subscriber (existing email, wrong Name) ## This one is not developed
        4.0 - New subscriber, proper information

        :param request:
        :param args:
        :param kwargs:
        :return:
        """

        generate_token = secrets.token_hex(16)

        form = SubscriberDataForm(request.POST, initial={'token': generate_token})

        self.context = {"form": form, "subscription_active": True}

        if 'one_service' in request.POST and request.POST.get('one_service') is not '' \
                and request.POST.get('one_service') is not None:
            request.session['one_service'] = request.POST.get('one_service')
            self.context['one_service'] = request.POST.get('one_service')
        else:
            if request.session.get('one_service', None) is not None:
                self.context['one_service'] = request.session['one_service']

        if 'subs_updates' in request.POST and request.POST.get('subs_updates') is not '' \
                and request.POST.get('subs_updates') is not None:
            self.context['subs_updates'] = request.POST.get('subs_updates')

        if 'service_specific' in request.POST and request.POST.get('service_specific') is not '' \
                and request.POST.get('service_specific') is not None:
            self.context['service_specific'] = bool(strtobool(request.POST.get('service_specific')))

        if 'object' in request.POST and request.POST.get('object') is not '' \
                and request.POST.get('object') is not None:
            request.session['object_passed'] = request.POST.get('object')
            self.context['object_passed'] = request.POST.get('object')
        else:
            if request.session.get('object_passed', None) is not None:
                self.context['object_passed'] = request.session['object_passed']

            if request.session.get('service_id', None) is not None:
                obj = get_object_or_404(Service, id=request.session['service_id'])
                self.context['object'] = obj
                self.context['service_id'] = request.session['service_id']

        # It requests to create a subscription
        if 'subs_updates' in request.POST:

            if form.is_valid():

                # Getting email entered by user
                email = form.cleaned_data['email']

                # Passing email to template
                self.context["subscriber_email"] = email

                # Getting name entered by the user
                name = form.cleaned_data['name']

                # Passing user name to template
                self.context["user_name"] = name

                # It verifies if the email belongs to the Email Domain list
                if not form.check_mail_domain():
                    self.context['email_domain_forbidden'] = True

                    # Getting list of approved domains
                    email_domain_list = EmailDomain.objects.all()

                    # Passing list ot template
                    self.context['email_domain_list'] = email_domain_list

                else:
                    if 'one_service' in request.POST:

                        service = None

                        if request.POST.get('object') is not '' and \
                                request.POST.get('object') is not None:
                            service = get_object_or_404(Service, id=request.POST['one_service'])
                        elif request.session.get('one_service', None) is not None:
                            service = get_object_or_404(Service, id=request.session['one_service'])

                        if service is not None:
                            form.cleaned_data['services'] = Service.objects.filter(name=service.name)

                        # If the user is not registered before save it
                        if not Subscriber.objects.filter(email=email).exists():

                            # HERE WE NEED TO VERIFY USER EMAIL FIRST
                            subscriber = form.save()
                            SubscriberDataForm.notify_user_email(form)
                            # Add service to the user account
                            subscriber.services.add(service)
                            subscriber.save()

                        else:
                            # If the user is already registered we just need to add the selected
                            # services and sub-services to the subscription
                            # Get user from database
                            user = Subscriber.objects.filter(email=email)[:1].get()

                            # Get user subservices
                            user_subservices = user.subservices.all()

                            # Get list of subservices to add
                            subservices_to_add = form.cleaned_data["subservices"]

                            # Add service to the user account
                            user.services.add(service)
                            user.save()

                            SubscriberDataForm.notify_user_email(form)

                            # Add subservices to the user account
                            for subservice_to_add in subservices_to_add:
                                if subservice_to_add not in user_subservices:
                                    user.subservices.add(subservice_to_add)
                                    user.save()

                        self.context['subscribed'] = True

                    else:
                        # If the user selected at least one service or subservice
                        if len(form.cleaned_data['services']) or \
                                len(form.cleaned_data['subservices']):
                            # If the user is not registered before save it
                            if not Subscriber.objects.filter(email=email).exists():
                                # HERE WE NEED TO VERIFY USER EMAIL FIRST
                                form.save()
                                SubscriberDataForm.notify_user_email(form)
                                self.context['subscribed'] = True
                            else:
                                # Here we know that the email exist,
                                # but we have not verified the username
                                self.context['user_exists'] = True
                                self.context['user_exists_email'] = email
                                self.context['updated_left'] = True

                        else:
                            self.context['no_selection'] = True
                            self.context['subscribed'] = False

        # It requests to update the subscription information
        # after having requested a subscription
        elif 'update_subs' in request.POST:

            # Getting the email entered by the user
            user_email = request.POST.get('user_email', None)

            if user_email:
                # Check if this email is registered for notifications
                if Subscriber.objects.filter(email=user_email).exists():

                    # Send the email with the link to update subscription
                    SubscriberForm.send_link_by_user_email(str(user_email))

                    # Email has been sent, update template
                    if request.POST.get('updated_left', None):
                        self.context['updated_left'] = True
                    else:
                        self.context['updated_right'] = True
                else:
                    self.context['not_registered'] = True
                    self.context['email_entered'] = user_email
            else:
                self.context['empty_email'] = True

        return render(request, self.template_name, self.context)


class ServiceHistoryView(View):
    """
    Services Status History Visualization page
    """

    template_name = "ss_history_visualization.html"

    def get(self, request, subservice_id=None, service_id=None, domain_id=None, *args, **kwargs):

        context = {"active_nav": 1, 'service_history_view': True}

        page_focus = None

        searching = False

        if subservice_id is None and service_id is None and domain_id is None:
            tickets_list = Ticket.objects.all().order_by('-pk')

            if 'search_tickets' in request.GET:
                search_value = request.GET['search']
                aux_list = list()

                if search_value is not '':
                    searching, tickets_list = set_search_context(aux_list, context, search_value, tickets_list)

                    if not tickets_list and not searching:
                        context['no_tickets'] = True

                    if not tickets_list and searching:
                        context['no_results'] = True

            context['tickets_list'] = tickets_list

        # Focus is on a Domain
        if domain_id is not None:
            obj = get_object_or_404(ClientDomain, id=domain_id)
            context['object'] = obj

            # Signal page is focused on Domain
            page_focus = "domain"

            tickets_list = Ticket.objects.none()

            for service in obj.services.all():
                # Getting all tickets affecting this service
                subservices = SubService.objects.filter(topology__service__name=service.name)
                # Initializing queryset to empty
                # for every subservice:
                for subservice in subservices:
                    queryset = Ticket.objects.filter(sub_service=subservice).order_by('-pk')
                    tickets_list = tickets_list.union(queryset)

            tickets_list = tickets_list.order_by('-pk')
            searching = self.set_search_request(context, request, searching, tickets_list)

        # Focus on service
        if service_id is not None:
            obj = get_object_or_404(Service, id=service_id)
            context['object'] = obj

            # Signal page is focused on Service
            page_focus = "service"

            # Getting all tickets affecting this service
            subservices = SubService.objects.filter(topology__service__name=obj.name)

            # Initializing queryset to empty
            tickets_list = Ticket.objects.none()

            # for every subservice:
            for subservice in subservices:
                queryset = Ticket.objects.filter(sub_service=subservice).order_by('-pk')
                if queryset:
                    tickets_list = tickets_list | queryset

            self.set_search_request(context, request, searching, tickets_list)

        # Focus on subservice
        if subservice_id is not None:
            obj = get_object_or_404(SubService, id=subservice_id)
            context['object'] = obj

            # Signal page is focused on Subservice
            page_focus = "subservice"

            # Initializing queryset to empty
            tickets_list = Ticket.objects.none()

            queryset = Ticket.objects.filter(sub_service=obj).order_by('-pk')
            if queryset:
                tickets_list = tickets_list | queryset

            self.set_search_request(context, request, searching, tickets_list)

        subservice_list = SubService.objects.all()
        context['available_subservices'] = subservice_list

        service_list = Service.objects.all()
        context['available_services'] = service_list

        domain_list = ClientDomain.objects.all()
        context['available_domains'] = domain_list

        # Assign a page focus
        context['page_focus'] = page_focus

        return render(request, self.template_name, context)

    @staticmethod
    def set_search_request(context, request, searching, tickets_list):

        if 'search_tickets' in request.GET:
            search_value = request.GET['search']
            aux_list = list()

            if search_value is not '':
                searching, tickets_list = set_search_context(aux_list, context, search_value,
                                                             tickets_list)
        context['tickets_list'] = tickets_list
        if not tickets_list and not searching:
            context['no_tickets'] = True
        if not tickets_list and searching:
            context['no_results'] = True
        return searching


def set_search_context(aux_list, context, search_value, tickets_list):

    for ticket in tickets_list:
        if (search_value.lower() in (ticket.ticket_id.lower()) or
                (search_value.lower() in ticket.action_description.lower()) or
                (search_value.lower() in ticket.status.tag.lower())):

            aux_list.append(ticket)
    tickets_list = aux_list
    searching = True
    context['search_value'] = search_value
    return searching, tickets_list


class ServiceHistoryDetailsView(ListView):
    """
    Services Status History Details page
    """

    template_name = "sh_details.html"

    def get(self, request, ticket_id=None, service_id=None, *args, **kwargs):

        context = {
            "active_nav": 1
        }

        if ticket_id is not None:

            # Getting ticket instance
            obj = get_object_or_404(Ticket, id=ticket_id)
            context['object'] = obj

            # Getting list of events associated with this ticket
            ticket_events = TicketLog.objects.filter(ticket=obj)
            context['ticket_events'] = ticket_events

            # Getting list of tickets associated with the service
            service_tickets = Ticket.objects.all()
            context['service_tickets'] = list(service_tickets)

            # Getting number of tickets
            count = service_tickets.count()
            context['tickets_count'] = count

            # Getting index of this ticket
            index = service_tickets.filter(id__lt=obj.id).count()
            context['ticket_index'] = index

            # Getting previous ticket
            prev = index - 1

            if prev > 0:
                ticket = service_tickets[prev]
                context['prev_ticket'] = ticket

            # Getting index of previous ticket
            _next = index + 1

            if _next <= count - 1:
                ticket = service_tickets[_next]
                context['next_ticket'] = ticket

            # List of clients, with services and associated subservices.
            # Manually associate subservice with service and domains, based on topography
            domain_list = ClientDomain.objects.all()
            associated_domains = []
            associated_services = []
            for domain in domain_list:
                for service in domain.services.all():
                    subservices = SubService.objects.filter(topology__service__name=service.name).all()
                    for ticketSub in obj.sub_service.all():
                        if ticketSub in subservices:
                            if domain not in associated_domains:
                                associated_domains.append(domain)
                            if service not in associated_services:
                                associated_services.append(service)
            context['ticket_domain'] = associated_domains
            context['ticket_services'] = associated_services

        if service_id is not None:
            obj = get_object_or_404(Service, id=service_id)
            context['service'] = obj

            # If service_id exists, clear next and previous ticket context
            context['prev_ticket'] = None
            context['next_ticket'] = None

            # Following section finds all tickets in same service
            # Getting all tickets affecting this service
            subservices = SubService.objects.filter(topology__service__name=obj.name)

            # Initializing queryset to empty
            tickets_list = Ticket.objects.none()

            # for every subservice:
            for subservice in subservices:
                queryset = Ticket.objects.filter(sub_service=subservice).order_by('pk')
                if queryset:
                    tickets_list = tickets_list.union(queryset)

            if 'search_tickets' in request.GET:
                search_value = request.GET['search']
                aux_list = list()

                if search_value is not '':
                    searching, tickets_list = set_search_context(aux_list, context, search_value,
                                                                 tickets_list)

            context['tickets_list'] = tickets_list

            # Find index of current page in tickets list.
            index = 0
            count = 0
            for ticket in tickets_list:
                if ticket.id == ticket_id:
                    index = count
                count = count + 1

            prev = index - 1

            if index > 0:
                ticket = tickets_list[prev]
                context['prev_ticket'] = ticket

            # Getting index of previous ticket
            i_next = index + 1

            # if i_next < tickets_list.count():
            if i_next < len(tickets_list):
                ticket = tickets_list[i_next]
                context['next_ticket'] = ticket

        return render(request, self.template_name, context)


class ModifyUserSubscription(ListView):
    """
    Modify Users Subscription page
    """

    template_name = "modify_subscription.html"

    # def get(self, request, email=None, token=None, *args, **kwargs):
    def get(self, request, email, token):

        # Getting user by token
        user = Subscriber.objects.filter(token=token)[:1].get()

        context = {
            'user': user
        }

        # Getting the services for this user
        user_services = user.services.all()

        if user_services:
            context['services'] = user_services
        else:
            context['no_services'] = True

        # Getting the subservices for this user
        user_sub_services = user.subservices.all()

        if user_sub_services:
            context['sub_services'] = user_sub_services
        else:
            context['no_subservices'] = True

        # Getting the services this user is not registered to
        queryset = Service.objects.all()
        services_not_registered = list()

        for service in queryset:
            if service not in user_services:
                services_not_registered.append(service)

        if services_not_registered:
            context['services_to_add'] = services_not_registered
        else:
            context['no_services_to_add'] = True

        # Getting the sub-services this user is not registered to
        queryset = SubService.objects.all()
        sub_services_not_registered = list()

        for sub_service in queryset:
            if sub_service not in user_sub_services:
                sub_services_not_registered.append(sub_service)

        if sub_services_not_registered:
            context['subservices_to_add'] = sub_services_not_registered
        else:
            context['no_subservices_to_add'] = True

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """
        Method to modify subscription.
        This will allow to add and remove services and sub-services
        """

        # Getting user by userID
        user_id = request.POST.get('user_id')
        user = Subscriber.objects.get(id=user_id)

        # Getting list of services to delete
        services_deleted = request.POST.getlist('selected_services')

        if services_deleted:
            # Deleting the services
            for service in services_deleted:
                model_service = Service.objects.filter(name=service)[:1].get()
                user.services.remove(model_service)

        # Getting list of sub_services to delete
        subservices_deleted = request.POST.getlist('selected_subservices')

        if subservices_deleted:
            # Deleting the subservices
            for subservice in subservices_deleted:
                model_subservice = SubService.objects.filter(name=subservice)[:1].get()
                user.subservices.remove(model_subservice)

        # Getting list of services to add
        services_added = request.POST.getlist('selected_services_to_add')

        if services_added:
            # Adding the services
            for service in services_added:
                model_service = Service.objects.filter(name=service)[:1].get()
                user.services.add(model_service)

        # Getting list of sub_services to add
        subservices_added = request.POST.getlist('selected_subservices_to_add')

        if subservices_added:
            # Adding the subservices
            for subservice in subservices_added:
                model_subservice = SubService.objects.filter(name=subservice)[:1].get()
                user.subservices.add(model_subservice)

        context = {
            'user': user,
            'services_list': services_deleted,
            'subservices_list': subservices_deleted,
            'services_list_added': services_added,
            'subservices_list_added': subservices_added
        }

        # If no changes were selected
        if not (services_deleted or subservices_deleted or services_added or subservices_added):
            context['no_changes'] = True
        else:
            context['completed'] = True

        return render(request, self.template_name, context)
