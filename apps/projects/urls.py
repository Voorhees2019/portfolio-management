from django.urls import path
from . import views


urlpatterns = [
    path('projects/', views.projects, name='projects'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<int:project_id>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:project_id>/delete/', views.project_delete, name='project_delete'),
    path('projects/public/', views.projects, name='projects_public'),
    path('projects/upload-csv/', views.upload_csv, name='upload_csv'),
    path('project/upload-csv/confirm/', views.confirm_upload_csv, name='confirm_upload_csv'),
    path('mysets/', views.mysets, name='mysets'),
]
