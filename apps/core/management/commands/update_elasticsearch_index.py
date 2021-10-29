from django.core.management.base import BaseCommand
from apps.projects.utils import create_or_update_elasticsearch_index


class Command(BaseCommand):
    help = 'Create or update ElasticSearch index'

    def handle(self, *args, **kwargs):
        create_or_update_elasticsearch_index()
