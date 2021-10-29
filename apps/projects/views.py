from typing import Union
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from .models import Project, Industry, Technology
from .utils import search_docs


def set_exact_objects_order(elastic_objs_ids: list, model: Union[Project, Industry, Technology]) -> list:
    """Returns list of objects in the exact order of returned elastic's sorted projects"""
    objects = []
    for elastic_obj_id in elastic_objs_ids:
        for obj in model.objects.filter(id__in=elastic_objs_ids):
            if obj.id == elastic_obj_id:
                objects.append(obj)
    return objects


def transform_aggregation(aggregation: dict, model: Union[Industry, Technology]) -> dict:
    """
    Retrieves objects' indices and doc_counts from aggregation and
    returns dict where key = postgres object, value = object's doc_count from aggregation
    """
    ids = [int(bucket.get('key')) for bucket in aggregation]
    doc_counts = [bucket.get('doc_count') for bucket in aggregation]
    objs = set_exact_objects_order(ids, model)
    d = {}
    for i in range(len(objs)):
        d.update({objs[i]: doc_counts[i]})
    return d


def get_additional_filters(unfiltered_agg: dict, filtered_agg: dict, selected_ids: list[int],
                           model: Union[Industry, Technology]) -> dict:
    """Subtracts filtered objects from unfiltered in order to get additional filters' count"""
    unfiltered_objs = transform_aggregation(unfiltered_agg, model)
    filtered_objs = transform_aggregation(filtered_agg, model)

    # get additional objects
    for obj, doc_count in unfiltered_objs.items():
        # skip selected objects
        if obj.id in selected_ids:
            continue
        # subtract filtered from unfiltered
        if obj in filtered_objs:
            unfiltered_objs[obj] = unfiltered_objs[obj] - filtered_objs[obj]

    # sort filters: at the top are selected ones and then additional filters in descending order
    unfiltered_objs = dict(sorted(unfiltered_objs.items(), key=lambda x: (x[0].id in selected_ids, x[1]), reverse=True))
    return unfiltered_objs


def projects(request):
    context = {}
    selected_industries_ids = list(map(int, request.GET.getlist('industries')))
    selected_technologies_ids = list(map(int, request.GET.getlist('technologies')))
    project_search_text = request.GET.get("search")

    # ElasticSearch query
    query = {
        "from": (int(request.GET.get('page', 1)) - 1) * settings.PAGE_SIZE,
        "size": settings.PAGE_SIZE,
        "query": {
            "bool": {
                "must": []
            }
        },
        "aggs": {
            "industries": {
                "terms": {
                    "field": "industries",
                    "size": 1000
                }
            },
            "technologies": {
                "terms": {
                    "field": "technologies",
                    "size": 1000
                }
            },
            "unfiltered_industries": {
                "global": {},
                "aggs": {
                    "all_industries": {
                        "aggs": {
                            "industries": {
                                "terms": {"field": "industries", "size": 1000}
                            }
                        },
                        "filter": {"match_all": {}}
                    }
                }
            },
            "unfiltered_technologies": {
                "global": {},
                "aggs": {
                    "all_technologies": {
                        "aggs": {
                            "technologies": {
                                "terms": {"field": "technologies", "size": 1000}
                            }
                        },
                        "filter": {"match_all": {}}
                    }
                }
            }
        }
    }

    if not selected_industries_ids and not selected_technologies_ids and not project_search_text:
        query['query'] = {"match_all": {}}

    if selected_industries_ids:
        context.update(selected_industries=selected_industries_ids)
        # add industries to query
        query['query']['bool']['must'].append({"terms": {"industries": selected_industries_ids}})
        # aggregation if no industries were checked
        if selected_technologies_ids:
            query['aggs']['unfiltered_industries']['aggs']['all_industries']['filter'] = {
                "bool": {
                    "must": [
                        {"terms": {"technologies": selected_technologies_ids}}
                    ]
                }
            }
        else:
            query['aggs']['unfiltered_industries']['aggs']['all_industries']['filter'] = {
                "match_all": {}
            }

    if selected_technologies_ids:
        context.update(selected_technologies=selected_technologies_ids)
        # add technologies to query
        query['query']['bool']['must'].append({"terms": {"technologies": selected_technologies_ids}})
        # aggregation if no technologies were checked
        if selected_industries_ids:
            query['aggs']['unfiltered_technologies']['aggs']['all_technologies']['filter'] = {
                "bool": {
                    "must": [
                        {"terms": {"industries": selected_industries_ids}}
                    ]
                }
            }
        else:
            query['aggs']['unfiltered_technologies']['aggs']['all_technologies']['filter'] = {
                "match_all": {}
            }

    if project_search_text:
        context.update(search_value=project_search_text)
        match_query = {
            "bool": {
                "should": [
                    {"match": {"title": project_search_text}},
                    {"match": {"description": project_search_text}}
                ]
            }
        }
        # add match fields to query
        query['query']['bool']['must'].append(match_query)
        # add match fields to unfiltered aggregations
        if selected_industries_ids:
            if selected_technologies_ids:
                query['aggs']['unfiltered_industries']['aggs']['all_industries']['filter']['bool']['must'].append(
                    match_query)
            else:
                query['aggs']['unfiltered_industries']['aggs']['all_industries']['filter'] = match_query
        if selected_technologies_ids:
            if selected_industries_ids:
                query['aggs']['unfiltered_technologies']['aggs']['all_technologies']['filter']['bool']['must'].append(
                    match_query)
            else:
                query['aggs']['unfiltered_technologies']['aggs']['all_technologies']['filter'] = match_query

    # process elastic query
    result = search_docs(query)
    project_count = result['hits']['total']['value']
    context.update(project_count=project_count)
    context.update(page_size=settings.PAGE_SIZE)

    project_list = []
    if result['hits']['hits']:
        proj_ids = [int(doc.get('_id')) for doc in result['hits']['hits']]
        project_list = set_exact_objects_order(proj_ids, Project)
    else:  # no matches found
        context.update(nothing_matched=True)
    context.update(projects=project_list)

    # process elastic unfiltered_industries aggregation
    if selected_industries_ids:
        # get additional industry filters
        industries = get_additional_filters(
            unfiltered_agg=result['aggregations']['unfiltered_industries']['all_industries']['industries'][
                'buckets'],
            filtered_agg=result['aggregations']['industries']['buckets'],
            selected_ids=selected_industries_ids,
            model=Industry
        )
    else:
        industries = transform_aggregation(result['aggregations']['industries']['buckets'], Industry)

    # process elastic unfiltered_technologies aggregation
    if selected_technologies_ids:
        # get additional technology filters
        technologies = get_additional_filters(
            unfiltered_agg=
            result['aggregations']['unfiltered_technologies']['all_technologies']['technologies'][
                'buckets'],
            filtered_agg=result['aggregations']['technologies']['buckets'],
            selected_ids=selected_technologies_ids,
            model=Technology
        )
    else:
        technologies = transform_aggregation(result['aggregations']['technologies']['buckets'], Technology)

    context.update(industries=industries)
    context.update(technologies=technologies)
    return render(request, 'projects/projects_list.html', context)


def mysets(request):
    return HttpResponse('here will be mysets')
