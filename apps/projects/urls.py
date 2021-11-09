from django.urls import path
from . import views


urlpatterns = [
    path('projects/', views.projects, name='projects'),
    path('projects/public/', views.projects, name='projects_public'),
    path('projects/upload-csv/', views.upload_csv, name='upload_csv'),
    path('project/upload-csv/confirm/', views.confirm_upload_csv, name='confirm_upload_csv'),
    path('mysets/', views.mysets, name='mysets'),
]
