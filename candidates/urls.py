from django.urls import path
from . import views

app_name = 'candidates'

urlpatterns = [
    path('', views.candidate_list, name='candidate_list'),
    path('create/', views.candidate_create, name='candidate_create'),
    path('<int:pk>/edit/', views.candidate_edit, name='candidate_edit'),
    path('<int:pk>/', views.candidate_profile, name='candidate_profile'),
    path('<int:pk>/delete/', views.candidate_delete, name='candidate_delete'),
    path('search/', views.search_candidates, name='search_candidates'),
    path('<int:candidate_id>/preview-resume/', views.preview_resume, name='preview_resume'),
    path('parse-cv/', views.parse_cv, name='parse_cv'),
] 