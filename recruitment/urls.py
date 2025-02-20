from django.urls import path
from . import views

app_name = 'recruitment'

urlpatterns = [
    path('', views.recruiting_process_list, name='process_list'),
    path('create/', views.recruiting_process_create, name='process_create'),
    path('<int:pk>/edit/', views.recruiting_process_edit, name='process_edit'),
    path('position/<int:position_id>/', views.position_recruiting_process, name='position_process'),
    path('position/<int:position_id>/candidate/<int:candidate_id>/', views.candidate_recruiting_process, name='candidate_process'),
    path('position/<int:position_id>/process/<int:process_id>/delete/', views.delete_recruiting_process, name='delete_process'),
    path('process/<int:process_id>/update-status/', views.update_recruiting_process_status, name='update_process_status'),
    path('position/<int:position_id>/stage/<str:stage_key>/candidates/', views.stage_candidates_api, name='stage_candidates_api'),
    path('pipeline/save-config/', views.save_pipeline_config, name='save_pipeline_config'),
] 