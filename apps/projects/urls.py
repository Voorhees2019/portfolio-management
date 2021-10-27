from django.urls import path
from . import views


urlpatterns = [
    path('projects/', views.projects, name='projects'),
    path('projects/public/', views.projects, name='projects_public'),
    path('mysets/', views.mysets, name='mysets'),
]
