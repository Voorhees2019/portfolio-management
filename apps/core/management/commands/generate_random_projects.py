from django.core.management.base import BaseCommand
from apps.projects.services import generate_fake_projects


class Command(BaseCommand):
    help = 'Create random projects'

    def add_arguments(self, parser):
        # Optional argument
        parser.add_argument('-n', '--number', type=int, help='Indicates the number of projects to be created')

    def handle(self, *args, **kwargs):
        number = kwargs['number']
        if number:
            generate_fake_projects(number)
        else:
            generate_fake_projects()
