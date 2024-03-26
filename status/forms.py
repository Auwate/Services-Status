import secrets

from django import forms
from django.core.exceptions import ValidationError
from validate_email import validate_email

from status.mail_sender import MailSender
from .models import ClientDomain
from .models import EmailDomain
from .models import Region
from .models import Service
from .models import SubService
from .models import Subscriber
from .models import Ticket
from .models import Topology


class ClientDomainForm(forms.ModelForm):

    def clean(self):

        # check to see if user has chosen a service
        if 'services' in self.cleaned_data:
            services = self.cleaned_data['services']

            # tmp_inter_services = []  # list to hold inter-domain services chosen by user

            for service in services:
                if service.scope == Service.INTER_DOMAIN:
                    # tmp_inter_services.append(service.name)

                    """
                    if user chose more than 1 inter-domain service
                    currently the feature is not needed, but will be
                    left here commented out if that feature is needed
                    in the future
                    """
                    # if len(tmp_inter_services) > 1:
                    #     self.add_error("services", "Only 1 inter-domain service can be chosen. \
                    #             Please choose between " + " and ".join(tmp_inter_services))
                    #     raise ValidationError("There are some errors in services")

                    # check if it is already taken by another client domain
                    if ClientDomain.objects.filter(services__in=[service]) \
                            .exclude(name=self.instance).exists():
                        self.add_error("services", "{} is an inter-domain service and has  \
                                    already been taken.".format(service))
                        raise ValidationError("There are some errors in services")


class EmailActions:

    @staticmethod
    def check_email_domain(domain):

        # It verifies the existence or not of that email domain
        domain_exist = EmailDomain.objects.filter(domain=domain).count()

        if domain_exist == 0:
            return False

        return True

    @staticmethod
    def notify_subscription_to_user_email(email, services, subservices):

        service_list = ''
        service_list_html = ''

        subservice_list = ''
        subservice_list_html = ''

        if len(services):
            service_list += '<br>'
            service_list_html += '<ul>'
            for service in services:
                service_list += f"""{service}<br>"""
                service_list_html += f"""<li>{service}</li>"""
            service_list += '<br>'
            service_list_html += '</ul>'
        else:
            service_list += '<br>None selected<br>'
            service_list_html += '<ul><li>None selected</li></ul>'

        if len(subservices):
            subservice_list += '<br>'
            subservice_list_html += '<ul>'
            for subservice in subservices:
                subservice_list += f"""{subservice}<br>"""
                subservice_list_html += f"""<li>{subservice}</li>"""
            subservice_list += '<br'
            subservice_list_html += '</ul>'
        else:
            subservice_list += '<br>None selected<br>'
            subservice_list_html += '<ul><li>None selected</li></ul>'

        # Email content
        text = f"""\
            You have subscribed to receive notifications from the following services:
            <br>
            {service_list}
            You have subscribed to receive notifications from the following sub-services:
            {subservice_list}"""

        html = f"""\
        <html>
            <body>
                <p>You have subscribed to receive notifications from the following Service(s)</p>
                {service_list_html}
                <p>You have subscribed to receive notifications from the following Sub-service(s)</p>
                {subservice_list_html}
            </body>
        </html>"""

        subject = "Subscription requested!"

        mail_sender = MailSender(html, subject, text, email)
        mail_sender.send_mail()

    @staticmethod
    def send_subscription_notification(email, token):

        hostname = 'https://status.amlight.net'
        view_path = '/subscriber'

        link = hostname + view_path + '/' + email + '/' + token

        # Email content
        text = f"""\
                                Link to modify your subscription:
                                {link}
                                """

        html = f"""\
                                <html>
                                  <body>
                                    <p>Link to modify your subscription<br>
                                    </p>
                                    <a href="{link}">Modify your subscription</a>
                                  </body>
                                </html>
                                """

        subject = "Modification requested on Subscription!"

        mail_sender = MailSender(html, subject, text, email)
        mail_sender.send_mail()

    @staticmethod
    def ticket_notification(sub_service_id, changed_data, cleaned_data, cleaned_data_ext=None):
        """
        Method in charge to control the ticket notification process
        :param sub_service_id:
        :param changed_data:
        :param cleaned_data:
        :param cleaned_data_ext: It will get all the data related to the ticket logs
        :return:
        """

        # It gets all the users who belong to that Sub Service

        # It gets the list of services that has that Sub Service
        services = Service.objects.filter(topology__subservices=sub_service_id)
        subservices = SubService.objects.filter(id=sub_service_id)

        # Information to use in the email Body
        region = Region.objects.filter(
            client_domains__services__topology__subservices__in=subservices
        )
        topology = Topology.objects.filter(subservices__in=subservices)

        _changed_data = changed_data

        users_mail1 = list()
        users_mail2 = list()

        if services.count() != 0:
            # It gets the list of Key ID ot those services
            users_mail1 = Subscriber.objects.filter(services__in=services)

            # Remove duplicates
            users_mail1 = list(dict.fromkeys(users_mail1))

        if subservices.count() != 0:
            users_mail2 = Subscriber.objects.filter(subservices__in=subservices)

            # Remove duplicates
            users_mail2 = list(dict.fromkeys(users_mail2))

        users = list(set(users_mail1) | set(users_mail2))

        data = dict()
        data['ticket_id'] = cleaned_data.get('ticket_id')
        data['region'] = 'None'
        if region.count() != 0:
            data['region'] = region[0].name
        data['priority'] = 'None'
        if topology.count() != 0:
            data['priority'] = topology[0].priority
        data['service'] = None
        if services.count() != 0:
            data['service'] = services[0].name
        data['subservice'] = 'None'
        if subservices.count() != 0:
            data['subservice'] = subservices[0].name

        for user in users:
            text = f"""\
                            Changes on the ticket {data['ticket_id']}:
                            Region: {data['region']}
                            Priority: {data['priority']}
                            Service: {data['service']}
                            Sub-Service: {data['subservice']}
                            """

            html = f"""\
                            <html>
                              <body>
                                <p>Changes on the ticket 
                                    <span style="font-weight: bold;">{data['ticket_id']}</span>:
                                    <br>
                                    <ul>
                                        <li>
                                            <span style="font-weight: bold;">Region:</span> {data['region']}
                                        </li>
                                        <li>
                                            <span style="font-weight: bold;">Priority:</span> {data['priority']}
                                        </li>
                                        <li>
                                            <span style="font-weight: bold;">Service:</span> {data['service']}
                                        </li>
                                        <li>
                                            <span style="font-weight: bold;">Sub-Service:</span> {data['subservice']}
                                        </li>
                                    </ul>
                                </p>
                              </body>
                            </html>
                            """

            subject = "Changes detected!"

            mail_sender = MailSender(html, subject, text, user.email)
            mail_sender.send_mail()


class TicketForm(forms.ModelForm):
    NO = False
    YES = True
    YES_NO_CHOICES = (
        (NO, 'No'),
        (YES, 'Yes')
    )

    cleaned_data = None

    class Meta:
        model = Ticket
        fields = '__all__'
        labels = {
            'begin' : "UTC-05:00",
            'end' : "UTC-05:00",
        }

    def __init__(self, *args, **kwargs):

        super(TicketForm, self).__init__(*args, **kwargs)

        if self.instance.id:
            self.fields['notify_action'] = forms.ChoiceField(choices=self.YES_NO_CHOICES)

    def clean(self):
        self.cleaned_data = super().clean()
        self.instance.user_notified = False

        if super().is_valid():

            begin = self.cleaned_data['begin'].strftime('%Y-%m-%d %H:%M:%S')

            if 'end' in self.cleaned_data and self.cleaned_data['end'] is not None:

                end = self.cleaned_data['end'].strftime('%Y-%m-%d %H:%M:%S')

                if begin > end:
                    self.add_error("begin",
                                   "The Begin date {} should follow a "
                                   "chronological order.".format(
                                       self.cleaned_data["begin"]))

                    self.add_error("end",
                                   "The End date {} should follow a "
                                   "chronological order.".format(
                                       self.cleaned_data["end"]))

                    raise ValidationError("There are some errors on the Ticket's dates.")

            if self.changed_data and (self.changed_data == ['notify_action'] and
                                      not self.instance.notify_action and
                                      self.cleaned_data['notify_action'] == 'True'):

                self.instance.notify_action = True

                try:
                    EmailActions.ticket_notification(self.cleaned_data['sub_service'].pk,
                                                     self.changed_data,
                                                     self.cleaned_data)
                    self.instance.user_notified = True

                except Exception as e:
                    print(e)  # we should log this as an error

            elif self.changed_data and self.changed_data != ['notify_action'] and \
                    (self.cleaned_data['notify_action'] is True or
                     self.cleaned_data['notify_action'] == 'True'):

                self.instance.notify_action = True

                try:
                    EmailActions.ticket_notification(self.cleaned_data['sub_service'].pk,
                                                     self.changed_data,
                                                     self.cleaned_data)
                    self.instance.user_notified = True
                except Exception as e:
                    print(e)  # we should log this as an error

            if self.cleaned_data['client_domains']:
                # all services under the domain are affected
                # all sub-services under each service is also
                # affected 
                
                for client_domain in self.cleaned_data['client_domains']:
                    # |= allows us to create a union of querysets
                    # This allows for us to add on to the services
                    # if the user already chooses a service or
                    # services.
                    self.cleaned_data['services'] |= client_domain.services.all()

            if self.cleaned_data['services']:
                # associated_sub_services

                services = self.cleaned_data['services']
                querysets = []
                for service in services:

                    # get sub service under service from Topology
                    if Topology.objects.filter(service=service).values('subservices').exists():
                        topology_queryset = Topology.objects.filter(
                            service=service)
                        for topology in topology_queryset:
                            querysets.append(topology.subservices.all())

                result_queryset = SubService.objects.none()
                for query in querysets:
                    result_queryset = result_queryset | query

                # |= allows us to create a union of querysets
                # This allows for us to add on to the subservices
                # if the user already chooses a sub-service or
                # sub-services.
                self.cleaned_data['sub_service'] |= result_queryset

            if not (self.cleaned_data['sub_service'].exists()):
                raise ValidationError("Please select one or more Client Domains, Services and/or Sub - Services")


class TicketHistoryInlineFormset(forms.models.BaseInlineFormSet):

    def __init__(self, *args, **kwargs):
        super(TicketHistoryInlineFormset, self).__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = False

    def clean(self):

        if super().is_valid():
            status_list = list()
            form_list = list()
            change_detected = False
            status = None
            main_begin = None
            cleaned_data = dict()
            cleaned_data_ext = list()
            changed_data = list()

            if self.data['begin_0'] and self.data['begin_1']:
                main_begin = self.data['begin_0'] + ' ' + self.data['begin_1']

            for form in self.forms:
                if form.cleaned_data != {}:
                    # Review this. I believe that this is an unreachable condition.
                    # If the form is valid, main begin will have always a value
                    if main_begin is None:
                        main_begin = form.cleaned_data.get('begin').strftime('%Y-%m-%d %H:%M:%S')

                    status = form.cleaned_data.get('status')
                    # Review this. I believe that this is an unreachable condition.
                    # If the form is valid, status will have always a value
                    if status is not None:
                        status_list.append(status.tag)
                    else:
                        break

                    if form.has_changed():
                        change_detected = True
                        changed_data.append(form.changed_data)

                        if 'ticket_id' not in cleaned_data:
                            cleaned_data.update({'ticket_id': form.instance.ticket})
                        cleaned_data_ext.append(form.cleaned_data)

                    form_list.append(form)

            if change_detected:

                my_raises = False

                for form in form_list:
                    begin = form.cleaned_data['action_date'].strftime('%Y-%m-%d %H:%M:%S')

                    if begin < main_begin:
                        form.add_error("action_date", "You can not have an action date "
                                                      "lower than the start day of the ticket {}.".
                                       format(form.cleaned_data["action_date"]))
                        my_raises = True

                if my_raises:
                    raise ValidationError("There are some errors on the Service's Status.")

                if not my_raises:
                    for form in form_list:
                        if [item for item in set(status_list) if status_list.count(item) > 1]. \
                                count('No Issues'):
                            if form.cleaned_data['status'].tag == 'No Issues':
                                form.add_error("status",
                                               "You can not have {} "
                                               "status multiple times.".
                                               format(form.cleaned_data["status"]))
                                my_raises = True

                if my_raises:
                    raise ValidationError("There are some errors on the Service's Status.")

                for form in form_list:
                    if status.tag != 'No Issues' and 'No Issues' in status_list \
                            and form.cleaned_data['status'].tag == 'No Issues':
                        form.add_error("status",
                                       "{} is an status available "
                                       "only as a final stage.".format(form.cleaned_data["status"]))
                        my_raises = True

                if my_raises:
                    raise ValidationError("There are some errors on the Service's Status.")

                if not self.instance.user_notified:
                    try:
                        EmailActions.ticket_notification(self.instance.sub_service_id,
                                                         changed_data,
                                                         cleaned_data,
                                                         cleaned_data_ext)
                    except Exception as e:
                        print(e)  # we should log this as an error


class SubscriberDataForm(forms.ModelForm):
    services = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=Service.objects.all(),
        required=False)

    subservices = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=SubService.objects.all(),
        required=False)

    name = forms.CharField(
        widget=forms.TextInput(
            attrs={"placeholder": "Full Name", "class": "form-control"}),
        max_length=40,
        required=True)

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"placeholder": "Email", "class": "form-control"}),
        required=True)

    def get_service_names(self):
        """
        Method to retrieve an array of service names
        """

        service_names = []
        for service in self.fields['services'].queryset:
            service_names.append(service.name)

        return service_names

    def filter_services(self, servs):
        """
        Method to filter the regions being retrieved and stored in the services variable
        """
        # If servs is empty, filter will return no selections
        if not servs:
            # Replace this with an error that will show up on the template.
            print("No matches for this Services filter")
            self.fields['services'].queryset = Service.objects.none()

        # Set filtered services to initial value of servs, then
        else:
            filtered_services = Service.objects.filter(name__icontains=servs[0])
            # qs1 = Service.objects.none()

            # Iterate through all values passed to servs and add them to the form's queryset.
            for service in servs:
                qs1 = Service.objects.filter(name__icontains=service)
                self.fields['services'].queryset = qs1 | filtered_services

    def check_mail_domain(self):
        """
        Method to check if the email provided belong to
        the list of user domains registered on the system
        """
        # Verify that the subscriber email belong to our domain list
        domain = self.cleaned_data["email"].split('@')[1]

        return EmailActions.check_email_domain(domain)

    def notify_user_email(self):
        """
        Method to send a mail notification
        about the subscription requested
        """
        email = self.cleaned_data["email"]
        services = self.cleaned_data["services"]
        subservices = self.cleaned_data["subservices"]

        EmailActions.notify_subscription_to_user_email(email, services, subservices)

    def clean(self):
        # Create token
        token = secrets.token_hex(64)

        # Update User's token
        self.cleaned_data["token"] = token

    class Meta:
        model = Subscriber
        fields = [
            'name',
            'email',
            'services',
            'subservices',
            'token'
        ]


class SubscriberForm(forms.ModelForm):
    """
    This methods is related with the insertion and update process that belong to the admin
    """

    class Meta:
        model = Subscriber
        fields = '__all__'

    def clean(self):

        cleaned_data = super().clean()

        email = cleaned_data['email']

        # Verify email authenticity
        is_valid = validate_email(email)

        # # Check if the host has SMTP Server and the email really exists:
        # pip install pyDNS
        # is_valid = validate_email(email, verify=True)

        if not is_valid:
            self.add_error("email", "{} is an invalid email information.".format(
                self.cleaned_data["email"]))
            raise ValidationError("There are some errors on the Subscriber's information.")

        # Verify that the subscriber email belong to our domain list
        domain = email.split('@')[1]

        # It verifies the existence or not of that email domain
        domain_exist = EmailDomain.objects.filter(domain=domain).count()

        if domain_exist == 0:
            self.add_error("email", "{} does not belong to our Users' domain.".format(
                self.cleaned_data["email"]))
            raise ValidationError("There are some errors on the Subscriber's information.")

        # Insert user and insert token
        if not self.instance.pk:

            # Create token
            token = secrets.token_hex(64)

            # Update User's token
            self.cleaned_data["token"] = token
        else:
            self.update_user_token()

        return self.cleaned_data

    @staticmethod
    def send_link_by_user_id(user_id):
        """
        Method to send a notification link given the User ID
        :param user_id:
        :return:
        """
        # It gets the user's email and token given its ID
        user = Subscriber.objects.filter(pk=user_id).values('email', 'token')

        email = user[0]['email']
        token = user[0]['token']

        EmailActions.send_subscription_notification(email, token)

    @staticmethod
    def send_link_by_user_email(_email):
        """
        Method to send a notification link given the User email
        :param _email:
        :return:
        """
        # It gets the user's token given its email
        user = Subscriber.objects.filter(email=_email).values('token')
        _token = str(user[0]['token'])  # Need to cast, otherwise it will have a nontype error

        EmailActions.send_subscription_notification(_email, _token)

    def update_user_token(self):
        """
        Method to update the user token after submitting its information
        This function was thought to be used considering the User ID as a reference
        :param:
        :return:
        """
        _token = secrets.token_hex(64)

        # It will be used on read only cases
        self.instance.token = _token

        # It will be used on no read only cases
        # self.cleaned_data["token"] = _token
