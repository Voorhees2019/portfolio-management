from typing import Union
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.fields.files import FieldFile
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.urls import reverse
from import_export.results import Result
from .models import Project, Industry, Technology, CSVFile
from .utils import search_docs
from tablib import import_set
from .admin import ProjectResource, process_before_import_row


class ProjectResourceFrontEnd(ProjectResource):
    def before_import_row(self, row, row_number=None, **kwargs):
        process_before_import_row(row, row_number, **kwargs)
        user_id = kwargs.get("user_id")
        row['author_id'] = user_id

    def get_instance(self, instance_loader, row):
        return Project.objects.filter(title=row.get('title'), author_id=row.get('author_id')).first()

    def init_instance(self, row=None):
        instance = super().init_instance(row)
        instance.author_id = row.get('author_id')
        return instance


def import_csv_file(file: Union[InMemoryUploadedFile, FieldFile], dry_run: bool, user_id: int) -> Result:
    project_resource = ProjectResourceFrontEnd()
    data = file.read().decode('utf-8')
    dataset = import_set(data, format='csv')
    return project_resource.import_data(dataset, dry_run=dry_run, user_id=user_id)


def set_exact_objects_order(elastic_objs_ids: list, model: Union[Project, Industry, Technology]) -> list:
    """Returns list of objects in the exact order of returned elastic's sorted projects"""
    objs_dict = {x.id: x for x in model.objects.filter(id__in=elastic_objs_ids)}
    objects = [objs_dict[i] for i in elastic_objs_ids if i in objs_dict]
    return objects


def transform_aggregation(aggregation: dict, model: Union[Industry, Technology]) -> list[
    list[Union[Industry, Technology, int]]]:
    """
    Retrieves objects' indices and doc_counts from aggregation and
    returns list of lists with postgres object and object's doc_count from aggregation
    """
    ids = [int(bucket.get('key')) for bucket in aggregation]
    doc_counts = [bucket.get('doc_count') for bucket in aggregation]
    objs = set_exact_objects_order(ids, model)
    return [[objs[i], doc_counts[i]] for i in range(len(objs))]


def get_additional_filters(unfiltered_agg: dict, filtered_agg: dict, selected_ids: list[int],
                           model: Union[Industry, Technology]) -> list:
    """Subtracts filtered doc_count from unfiltered doc_dount in corresponding aggregations
    in order to get additional filters' count"""
    unfiltered_list = transform_aggregation(unfiltered_agg, model)
    filtered_list = transform_aggregation(filtered_agg, model)

    for i, (unfiltered_obj, doc_count) in enumerate(unfiltered_list):
        # skip selected objects
        if unfiltered_obj.id in selected_ids:
            continue
        if unfiltered_obj in [sublist[0] for sublist in filtered_list]:
            # find index of sublist with unfiltered_obj in filtered_list
            for sublist_index in range(len(filtered_list)):
                if filtered_list[sublist_index][0] == unfiltered_obj:
                    # subtract filtered from unfiltered doc_count
                    unfiltered_list[i][1] = unfiltered_list[i][1] - filtered_list[sublist_index][1]
                    break

    # sort filters: at the top are selected ones and then additional filters in descending order
    unfiltered_list = sorted(unfiltered_list, key=lambda x: (x[0].id in selected_ids, x[1]), reverse=True)
    return unfiltered_list


@login_required
def projects(request):
    context = {}
    selected_industries_ids = list(map(int, request.GET.getlist('industries')))
    selected_technologies_ids = list(map(int, request.GET.getlist('technologies')))
    project_search_text = request.GET.get("search")

    # ElasticSearch query
    author_filter = {"terms": {"author": [request.user.id]}}
    query = {
        "from": (int(request.GET.get('page', 1)) - 1) * settings.PAGE_SIZE,
        "size": settings.PAGE_SIZE,
        "query": {
            "bool": {
                "must": [author_filter]
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
                        "filter": {
                            "bool": {
                                "must": [author_filter]
                            }
                        }
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
                        "filter": {
                            "bool": {
                                "must": [author_filter]
                            }
                        }
                    }
                }
            }
        }
    }

    if selected_industries_ids:
        context.update(selected_industries=selected_industries_ids)
        # add industries to query
        query['query']['bool']['must'].append({"terms": {"industries": selected_industries_ids}})
        # aggregation if no industries were checked
        if selected_technologies_ids:
            query['aggs']['unfiltered_industries']['aggs']['all_industries']['filter']['bool']['must'].append(
                {"terms": {"technologies": selected_technologies_ids}}
            )

    if selected_technologies_ids:
        context.update(selected_technologies=selected_technologies_ids)
        # add technologies to query
        query['query']['bool']['must'].append({"terms": {"technologies": selected_technologies_ids}})
        # aggregation if no technologies were checked
        if selected_industries_ids:
            query['aggs']['unfiltered_technologies']['aggs']['all_technologies']['filter']['bool']['must'].append(
                {"terms": {"industries": selected_industries_ids}}
            )

    if project_search_text:
        context.update(search_value=project_search_text)
        search_text_query = {
            "bool": {
                "should": [
                    {"match": {"title": project_search_text}},
                    {"match": {"description": project_search_text}}
                ]
            }
        }
        # add search fields to query
        query['query']['bool']['must'].append(search_text_query)
        # add search fields to unfiltered aggregations
        query['aggs']['unfiltered_industries']['aggs']['all_industries']['filter']['bool']['must'].append(
            search_text_query)
        query['aggs']['unfiltered_technologies']['aggs']['all_technologies']['filter']['bool']['must'].append(
            search_text_query)

    # process elastic query
    result = search_docs(query)
    project_count = result['hits']['total']['value']
    context.update(project_count=project_count)
    context.update(page_size=settings.PAGE_SIZE)

    project_list = []
    if result['hits']['hits']:
        proj_ids = [int(doc.get('_id')) for doc in result['hits']['hits']]
        project_list = set_exact_objects_order(proj_ids, Project)
    elif Project.objects.count() != 0:  # pass `no_search_result` to the template if there is any project in database
        context.update(no_search_result=True)
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

    if request.path == reverse('projects'):
        context.update(current_tab='private')
    elif request.path == reverse('projects_public'):
        context.update(current_tab='public')

    return render(request, 'projects/projects_list.html', context)


@login_required
def mysets(request):
    return HttpResponse('here will be mysets')


@login_required
def upload_csv(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('input_file')
        if not uploaded_file:
            messages.error(request, 'Empty field. You must upload .csv file')
            return render(request, 'projects/upload_csv.html', {})
        elif not uploaded_file.name.endswith('.csv'):
            messages.error(request, 'Incorrect file type. You must upload .csv file')
            return render(request, 'projects/upload_csv.html', {})

        csv_file = CSVFile(csv_file=uploaded_file)
        csv_file.author = request.user
        csv_file.save()

        uploaded_file.seek(0)  # to be able to read file again from the start
        result = import_csv_file(file=uploaded_file, dry_run=True, user_id=request.user.id)
        return render(request, 'projects/upload_csv_confirm.html', {'result': result, 'file_id': csv_file.id})
    return render(request, 'projects/upload_csv.html', {})


@login_required
def confirm_upload_csv(request):
    file_id = request.POST.get('file_id')
    file_obj = get_object_or_404(CSVFile, id=file_id)
    import_csv_file(file=file_obj.csv_file, dry_run=False, user_id=file_obj.author.id)
    messages.success(request, 'Your projects were successfully uploaded')
    return redirect('projects')
