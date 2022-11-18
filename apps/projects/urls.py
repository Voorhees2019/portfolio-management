from django.urls import path
from . import views

urlpatterns = [
    path('projects/', views.projects, name='projects'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/delete/', views.projects_delete, name='projects_delete'),
    path('projects/<int:project_id>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:project_id>/delete/', views.project_delete, name='project_delete'),
    path('projects/public/', views.projects, name='projects_public'),
    path('projects/upload-csv/', views.upload_csv, name='upload_csv'),
    path('project/upload-csv/confirm/', views.confirm_upload_csv, name='confirm_upload_csv'),
    path('mysets/', views.mysets, name='mysets'),
    path('mysets/create/', views.myset_create, name='myset_create'),
    path('mysets/delete/', views.mysets_delete, name='mysets_delete'),
    path('mysets/<int:set_id>/add_project/', views.myset_add_project, name='myset_add_project'),
    path('mysets/<int:set_id>/rename/', views.myset_rename, name='myset_rename'),
    path('mysets/<int:set_id>/copy/', views.myset_copy, name='myset_copy'),
    path('mysets/<int:set_id>/delete/', views.myset_delete, name='myset_delete'),
    path('mysets/<int:set_id>/projects/<int:project_id>/edit/', views.myset_project_edit, name='myset_project_edit'),
    path('mysets/<int:set_id>/projects/<int:project_id>/delete/', views.myset_project_delete, name='myset_project_delete'),
    path('mysets/<int:set_id>/shared/create/', views.myset_create_shared_link, name='myset_create_shared_link'),
    path('mysets/shared/<str:token>/', views.myset_shared_link, name='myset_shared_link'),
]
