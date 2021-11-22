from .models import Project
from elasticsearch import Elasticsearch
from django.conf import settings


es = Elasticsearch(hosts=settings.ELASTICSEARCH_URLS)


def create_index(index_name='projects'):
    mapping = {
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "description": {"type": "text"},
                "author": {"type": "keyword"},
                "project_id": {"type": "long"},
                "is_private": {"type": "boolean"},
                "industries": {"type": "keyword"},
                "technologies": {"type": "keyword"}
            }
        }
    }
    es.indices.create(index=index_name, body=mapping)


def search_docs(query, index_name='projects'):
    return es.search(index=index_name, body=query)


def refresh_elastic_index(index_name='projects'):
    if es.indices.exists(index=index_name):
        es.indices.refresh(index=index_name)


def update_elastic_document(obj, index_name='projects', refresh_index=True):
    if not es.indices.exists(index=index_name):
        create_index(index_name)
    project_doc = obj.get_elasticsearch_document()
    es.index(index=index_name, id=obj.id, document=project_doc)
    if refresh_index:
        refresh_elastic_index(index_name)


def delete_elastic_document(obj, index_name='projects', refresh_index=True):
    es.delete(index=index_name, id=obj.id, ignore=[400, 404])
    if refresh_index:
        refresh_elastic_index(index_name)


def update_elastic_index(index_name='projects'):
    if 'project_id' not in es.indices.get_mapping(index=index_name)[index_name]['mappings']['properties']:
        additional_properties = {
            "properties": {
                "project_id": {"type": "long"}
            }
        }
        es.indices.put_mapping(index=index_name, body=additional_properties)
    for project in Project.objects.all():
        update_elastic_document(project, index_name=index_name, refresh_index=False)
    refresh_elastic_index(index_name)
