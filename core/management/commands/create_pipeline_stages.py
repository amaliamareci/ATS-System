from django.core.management.base import BaseCommand
from core.models import Client

class Command(BaseCommand):
    help = 'Creates default pipeline stages for all clients that don\'t have them'

    def handle(self, *args, **options):
        clients = Client.objects.all()
        for client in clients:
            if not client.pipeline_stages.exists():
                client.create_default_pipeline_stages()
                self.stdout.write(self.style.SUCCESS(f'Created pipeline stages for {client.name}')) 