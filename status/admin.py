from django.contrib import admin
from django_admin_listfilter_dropdown.filters import ChoiceDropdownFilter, DropdownFilter, RelatedDropdownFilter

from status.forms import TicketHistoryInlineFormset, TicketForm, SubscriberForm, ClientDomainForm
from .models import ClientDomain
from .models import EmailDomain
from .models import Priority
from .models import Region
from .models import Service
from .models import Status
from .models import SubService
from .models import Subscriber
from .models import Ticket
from .models import TicketLog
from .models import Topology


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description',)
    search_fields = ['name', 'region_description', 'services__name']
    list_filter = (('client_domains__services__topology__subservices__ticket__status__tag',
                    DropdownFilter),
                   ('client_domains__name',
                    DropdownFilter),
                   ('client_domains__services__name',
                    DropdownFilter),
                   ('client_domains__services__topology__subservices__name',
                    DropdownFilter))
    ordering = ['name']


@admin.register(ClientDomain)
class ClientDomainAdmin(admin.ModelAdmin):
    form = ClientDomainForm
    list_display = ('name', 'description',)
    search_fields = ['name', 'domain_description']
    list_filter = (('services__topology__subservices__ticket__status__tag',
                    DropdownFilter),
                   ('region__name',
                    DropdownFilter),
                   ('services__name',
                    DropdownFilter),
                   ('services__topology__subservices__name',
                    DropdownFilter),
                   ('services__scope',
                    DropdownFilter))
    ordering = ['name']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'scope')
    search_fields = ['name', 'service_description', 'topology__subservices__name',
                     'clientdomain__region__name']
    list_filter = (('topology__subservices__ticket__status__tag',
                    DropdownFilter),
                   ('clientdomain__region__name',
                    DropdownFilter),
                   ('clientdomain__name',
                    DropdownFilter),
                   ('topology__subservices__name',
                    DropdownFilter),
                   ('scope',
                    ChoiceDropdownFilter))
    ordering = ['name']


@admin.register(SubService)
class SubServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'description',)
    search_fields = ['name', 'subservice_description', 'topology__service__name',
                     'topology__service__clientdomain__region__name']
    list_filter = (('ticket__status__tag',
                    DropdownFilter),
                   ('topology__service__clientdomain__region__name',
                    DropdownFilter),
                   ('topology__service__clientdomain__name',
                    DropdownFilter),
                   ('topology__service',
                    RelatedDropdownFilter))
    ordering = ['name']


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('tag', 'color_name', 'color_hex', 'class_design')
    ordering = ['tag']


def notify_users(modeladmin, request, queryset):
    queryset.update(notify_action=True)


notify_users.short_description = "Notify users about ticket"


def notify_action(obj):
    return obj


notify_action.short_description = 'Name'


class TicketHistoryInline(admin.StackedInline):
    model = TicketLog
    formset = TicketHistoryInlineFormset
    extra = 0
    ordering = ("action_date",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    # list_display = ('ticket_id', 'get_subservices', 'status', 'begin', 'end', 'notify_action',)
    list_display = ('ticket_id', 'subservices_list', 'status', 'begin', 'end', 'notify_action',)

    # def get_subservices(self, obj):
    #     return "\n".join([sub_service.name for sub_service in obj.sub_service.all()])
    #
    # get_subservices.short_description = 'Sub-Services'

    fieldsets = [
        ('Sub-Service on process', {'fields': ['ticket_id', 'client_domains', 'services', 'sub_service', 'status']}),
        ('Date information', {'fields': ['begin', 'end']}),
        ('Additional Information', {'fields': ['action_description', 'action_notes']}),
        (None, {'fields': ['notify_action']}),
    ]

    inlines = [TicketHistoryInline]

    # ticket id will be auto generated when landing on Add Ticket
    readonly_fields = ['ticket_id']

    search_fields = ['sub_service__name', 'status__tag']  # removed ticket_id 6/29

    list_filter = (('status',
                    RelatedDropdownFilter),
                   ('sub_service__topology__service__clientdomain__region__name',
                    DropdownFilter),
                   ('sub_service__topology__service__clientdomain__name',
                    DropdownFilter),
                   ('sub_service__topology__service__name',
                    DropdownFilter),
                   ('sub_service',
                    RelatedDropdownFilter))
    ordering = ['begin']

    actions = [notify_users]

    form = TicketForm

    def save_formset(self, request, form, formset, change):

        # If it is received data related to the ticket's events, the ticket
        # will update its status with the last status registered on the events
        if formset.cleaned_data:
            status = formset.cleaned_data[-1]['status']

            # If the last Ticket Log status is 'No Issues,' means that the problem has
            # updating the Ticket End Time to the value specified on the last Ticket Events
            if status.tag == 'No Issues':
                form.instance.end = formset.cleaned_data[-1]['action_date']
            status_category_id = Status.objects.get(tag=status)
            form.instance.category_status_id = status_category_id.pk
            form.instance.save()
        formset.save()


@admin.register(Subscriber)
class SubscribersAdmin(admin.ModelAdmin):
    """
    Class to support the Subscriber module registering on the admin

    It is created a form relation between this subscription
    and the SubscriberForm form
    """

    list_display = ('name', 'email')

    list_filter = (('services__clientdomain__region__name',
                    DropdownFilter),
                   ('services__clientdomain__name',
                    DropdownFilter),
                   ('services__name',
                    DropdownFilter),
                   ('subservices__name',
                    DropdownFilter)
                   )
    search_fields = ['name', 'email']
    ordering = ['name']

    readonly_fields = ['token']

    form = SubscriberForm


@admin.register(Topology)
class TopologyAdmin(admin.ModelAdmin):
    """
    Class to support the Topology module registering on the admin
    """

    list_display = ('service', 'subservices_list', 'priority',)
    list_filter = (('priority',
                    RelatedDropdownFilter),
                   ('subservices__ticket__status__tag',
                    DropdownFilter),
                   ('service__clientdomain__region__name',
                    DropdownFilter),
                   ('service__clientdomain__name',
                    DropdownFilter),
                   ('service',
                    RelatedDropdownFilter),
                   ('subservices',
                    RelatedDropdownFilter))
    search_fields = ['service', 'subservices', 'priority']
    ordering = ['service']


@admin.register(Priority)
class PriorityAdmin(admin.ModelAdmin):
    """
    Class to support the Priority module registering on the admin
    """

    list_display = ('tag', 'color', 'color_hex')
    ordering = ['tag']


@admin.register(EmailDomain)
class EmailDomainAdmin(admin.ModelAdmin):
    """
    Class to support the EmailDomain module registering on the admin
    """

    list_display = ('domain', 'description')
    search_fields = ['domain', 'domain_description']
    ordering = ['domain']
