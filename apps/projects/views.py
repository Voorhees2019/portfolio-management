from django.shortcuts import render
from django.http import HttpResponse
from .models import Project, Industry, Technology
from django.db.models import Count


def projects(request):
    project_list = Project.objects.filter(author=request.user)
    industry_list = Industry.objects.annotate(count=Count('project')).order_by('-count')
    technology_list = Technology.objects.annotate(count=Count('project')).order_by('-count')
    context = {'projects': project_list,
               'industry_list': industry_list,
               'technology_list': technology_list}
    return render(request, 'projects/projects_list.html', context)


def mysets(request):
    return HttpResponse('here will be mysets')
