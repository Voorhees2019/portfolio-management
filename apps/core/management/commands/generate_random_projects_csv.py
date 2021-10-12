from django.core.management.base import BaseCommand
from apps.projects.services import generate_fake_projects, generate_projects_csv


class Command(BaseCommand):
    help = 'Generate a random projects csv file'

    def add_arguments(self, parser):
        # optional argument
        parser.add_argument('-r', '--rows', type=int, help='Indicates the number of rows to be created')

    def handle(self, *args, **kwargs):
        rows = kwargs['rows']
        if rows:
            generate_projects_csv(rows)
        else:
            generate_projects_csv()
