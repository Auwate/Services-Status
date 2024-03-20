from django.core.management.base import BaseCommand
from status.models import Status

class Command(BaseCommand):
        
        help = 'Creates the initial objects required to start the service-status application'
        
        def handle(self, *args, **options):
                
                if Status.objects.count() > 0:
                        return
                
                initial_objects = [
                        {"tag":"Alert", "color_name": "Orange", "color_hex":"#FC810D", "class_design": "fas fa-exclamation-circle"},
                        {"tag":"In Process", "color_name": "Yellow", "color_hex":"#DBBF07", "class_design": "fas fa-tools"},
                        {"tag":"No Issues", "color_name": "Green", "color_hex":"#0AC739", "class_design": "fas fa-check-circle"},
                        {"tag":"Outage", "color_name": "Red", "color_hex":"#F00004", "class_design": "fas fa-times-circle"},
                        {"tag":"Planned", "color_name": "Blue", "color_hex":"#041DBF", "class_design": "far fa-calendar-alt"}
                ]
                
                for data_objects in initial_objects:
                    Status.objects.create(**data_objects)
