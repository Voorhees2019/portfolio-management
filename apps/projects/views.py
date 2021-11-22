from typing import Union
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.fields.files import FieldFile
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from import_export.results import Result
from .models import Project, Industry, Technology, CSVFile, Set
from .utils import search_docs
from tablib import import_set
from .admin import ProjectResource, process_before_import_row
from .forms import ProjectForm, SetForm


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


def get_projects_ids_from_cookies(cookies: dict) -> list:
    project_ids = cookies.get('project_ids')
    return [int(x) for x in project_ids.split('|')] if project_ids else []


def add_cookies(response: Union[HttpResponse, HttpResponseRedirect], cookies: dict):
    for cname, val in cookies.items():
        response.set_cookie(cname, val)


def delete_cookies(response: Union[HttpResponse, HttpResponseRedirect], cookies: list):
    for cname in cookies:
        response.delete_cookie(cname)


def clone_project(project: Project):
    old_industries = project.industries.all()
    old_technologies = project.technologies.all()
    project.pk = None
    # do not put the copied project into elastic index
    project.save(refresh_index=False, dry_index_update=True)
    project.is_original = False
    project.save(refresh_index=False, dry_index_update=True)
    project.industries.set(old_industries)
    project.technologies.set(old_technologies)
    return project


@login_required
def projects(request):
    context = {}
    selected_industries_ids = list(map(int, request.GET.getlist('industries')))
    selected_technologies_ids = list(map(int, request.GET.getlist('technologies')))
    project_search_text = request.GET.get("search")
    public_projects_filter = False

    if request.path == reverse('projects'):
        context.update(current_tab='private')
    elif request.path == reverse('projects_public'):
        context.update(current_tab='public')
        public_projects_filter = {"term": {"is_private": False}}

    # ElasticSearch query
    author_filter = {"terms": {"author": [request.user.id]}}
    public_or_author_filter = [public_projects_filter or author_filter]
    query = {
        "from": (int(request.GET.get('page', 1)) - 1) * settings.PAGE_SIZE,
        "size": settings.PAGE_SIZE,
        "sort": [
            {"project_id": {"order": "desc"}}
        ],
        "query": {
            "bool": {
                "must": public_or_author_filter
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
                                "must": public_or_author_filter
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
                                "must": public_or_author_filter
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
                    {"match_phrase_prefix": {"title": project_search_text}},
                    {"match_phrase_prefix": {"description": project_search_text}}
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
    return render(request, 'projects/projects_list.html', context)


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


@login_required
def project_edit(request, project_id):
    project = get_object_or_404(Project, id=project_id, author=request.user)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()  # no need to call `form.save_m2m()`. `save_m2m()` is only required if use `save(commit=false)`
            return redirect('projects')
    else:
        form = ProjectForm(instance=project)
    return render(request, 'projects/project_form.html', {'project': project, 'form': form})


@login_required
def project_delete(request, project_id):
    project = get_object_or_404(Project, id=project_id, author=request.user)
    project.delete()
    return redirect('projects')


@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            new_project = form.save(commit=False)
            new_project.author = request.user
            new_project.save()
            form.save_m2m()
            return redirect('projects')
    else:
        form = ProjectForm()
    return render(request, 'projects/project_form.html', {'form': form})


@login_required
def projects_delete(request):
    Project.objects.filter(author=request.user).delete()
    return redirect('projects')


@login_required
def mysets(request):
    context = {'sets': Set.objects.filter(author=request.user), 'current_tab': 'mysets'}
    return render(request, 'projects/mysets.html', context)


@login_required
def myset_create(request):
    if request.method == 'POST':
        form = SetForm(request.POST, author=request.user)
        if form.is_valid():
            new_set = form.save(commit=False)
            new_set.author = request.user
            new_set.save()
            # retrieve project ids from cookies and add projects to set
            project_ids = get_projects_ids_from_cookies(request.COOKIES)
            new_set.projects.set(project_ids)
            return HttpResponse('created')
    else:
        form = SetForm(author=request.user)
    return HttpResponse(form.as_p())


@login_required
def mysets_delete(request):
    Set.objects.filter(author=request.user).delete()
    return redirect('mysets')


@login_required
def myset_add_project(request, set_id):
    set_obj = get_object_or_404(Set, id=set_id, author=request.user)
    if request.method == 'POST':
        project_ids = get_projects_ids_from_cookies(request.COOKIES)
        set_obj.projects.set(project_ids)

        response = HttpResponse('success')
        messages.success(request, 'Your set has been successfully updated')
        # clear cookies
        delete_cookies(response, ['update_set', 'set_id', 'project_ids'])
        return response
    # GET request
    # retrieve sets' project ids and write to cookies
    projects_ids = list(set_obj.projects.values_list('id', flat=True))
    projects_ids = '|'.join(str(proj_id) for proj_id in projects_ids)

    response = redirect('projects')
    additional_cookies = {'update_set': 'yes', 'set_id': set_id, 'project_ids': projects_ids}
    add_cookies(response, additional_cookies)
    return response


@login_required
def myset_rename(request, set_id):
    set_obj = get_object_or_404(Set, id=set_id, author=request.user)
    if request.method == 'POST':
        form = SetForm(request.POST, instance=set_obj, author=request.user)
        if form.is_valid():
            form.save()
            return HttpResponse('success')
    else:
        form = SetForm(instance=set_obj, author=request.user)
    return HttpResponse(form.as_p())


@login_required
def myset_copy(request, set_id):
    set_obj = get_object_or_404(Set, id=set_id, author=request.user)
    new_set_name = f'Copy of {set_obj.name}'
    project_ids = []
    # if the set with such name already exists
    if Set.objects.filter(name=new_set_name, author=request.user).first():
        messages.error(request, f'Copy of this set already exists. Check your set list for "{new_set_name}".')
        return redirect('mysets')

    # clone all not original projects in order to avoid changing these
    # projects in copied sets, when editing these projects in original set
    for project in set_obj.projects.all():
        if not project.is_original:
            project_copy = clone_project(project)
            project_ids.append(project_copy.id)
        else:
            project_ids.append(project.id)
    # create a new set
    set_obj.pk = None
    set_obj.name = new_set_name
    set_obj.save()
    set_obj.projects.set(project_ids)
    return redirect('mysets')


@login_required
def myset_delete(request, set_id):
    set_obj = get_object_or_404(Set, id=set_id, author=request.user)
    set_obj.delete()
    return redirect('mysets')


@login_required
def myset_project_edit(request, set_id, project_id):
    from .forms import InSetEditProjectForm
    set_obj = get_object_or_404(Set, id=set_id, author=request.user)
    project = get_object_or_404(Project, id=project_id)

    if request.method == 'POST':
        # Copy project instance if it is original and edit only this copy
        if project.is_original:
            # Remove original project from set
            set_obj.projects.remove(project)
            # Copy project
            project = clone_project(project)
            # Add copied project to set
            set_obj.projects.add(project)

        form = InSetEditProjectForm(request.POST, instance=project)
        if form.is_valid():
            edited_project = form.save(commit=False)
            edited_project.save(refresh_index=False, dry_index_update=True)
            form.save_m2m()  # save related industries and technologies
            return redirect('mysets')
    else:  # need this 'else' in order to return form object with errors if form was invalid
        form = InSetEditProjectForm(instance=project)
    return render(request, 'projects/project_form.html', {'project': project, 'form': form})


@login_required
def myset_project_delete(request, set_id, project_id):
    set_obj = get_object_or_404(Set, id=set_id, author=request.user)
    project = get_object_or_404(Project, id=project_id)
    if project.is_original:
        set_obj.projects.remove(project)
    else:  # delete project if it's not original
        project.delete()
    # Delete set if there are no projects inside
    if not set_obj.projects.exists():
        set_obj.delete()
    return redirect('mysets')
