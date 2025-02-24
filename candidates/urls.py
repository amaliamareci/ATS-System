from django.urls import path
from . import views

app_name = 'candidates'

urlpatterns = [
    path('', views.candidate_list, name='candidate_list'),
    path('create/', views.candidate_create, name='candidate_create'),
    path('edit/<int:pk>/', views.candidate_edit, name='candidate_edit'),
    path('profile/<int:pk>/', views.candidate_profile, name='candidate_profile'),
    path('delete/<int:pk>/', views.candidate_delete, name='candidate_delete'),
    path('search/', views.search_candidates, name='search_candidates'),
    path('preview-resume/<int:candidate_id>/', views.preview_resume, name='preview_resume'),
    path('parse-cv/', views.parse_cv, name='parse_cv'),
    path('<int:candidate_id>/technical-notes/add/', views.add_technical_note, name='add_technical_note'),
    path('<int:candidate_id>/technical-notes/<int:note_id>/delete/', views.delete_technical_note, name='delete_technical_note'),
] 