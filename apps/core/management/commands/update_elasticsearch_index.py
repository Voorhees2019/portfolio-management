from django.core.management.base import BaseCommand
from apps.projects.utils import update_elastic_index


class Command(BaseCommand):
    help = 'Create or update ElasticSearch index'

    def handle(self, *args, **kwargs):
        update_elastic_index()
