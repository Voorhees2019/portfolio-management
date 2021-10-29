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
                "industries": {"type": "keyword"},
                "technologies": {"type": "keyword"}
            }
        }
    }
    es.indices.create(index=index_name, body=mapping)


def search_docs(query, index_name='projects'):
    return es.search(index=index_name, body=query)


def update_elastic_document(obj, index_name='projects'):
    if not es.indices.exists(index=index_name):
        create_index(index_name)
    project_doc = obj.get_elasticsearch_document()
    es.index(index=index_name, id=obj.id, document=project_doc)
    es.indices.refresh(index=index_name)


def delete_elastic_document(obj, index_name='projects'):
    es.delete(index=index_name, id=obj.id)
    es.indices.refresh(index=index_name)


def populate_index(index_name='projects'):
    for project in Project.objects.all():
        project_doc = project.get_elasticsearch_document()
        es.index(index=index_name, id=project.id, document=project_doc)
    es.indices.refresh(index=index_name)


def create_or_update_elasticsearch_index(index_name='projects'):
    if es.indices.exists(index=index_name):
        # update index
        populate_index(index_name)
    else:
        create_index(index_name)
        # fill the index with projects
        populate_index(index_name)
