from django.core.management.base import BaseCommand
from apps.projects.services import generate_fake_projects


class Command(BaseCommand):
    help = 'Create random projects'

    def add_arguments(self, parser):
        parser.add_argument('total', type=int, help='Indicates the number of projects to be created')

    def handle(self, *args, **kwargs):
        total = kwargs['total']
        generate_fake_projects(total)
