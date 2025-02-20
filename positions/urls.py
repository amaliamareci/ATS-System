from django.urls import path
from . import views

app_name = 'positions'

urlpatterns = [
    path('', views.position_list, name='position_list'),
    path('create/', views.position_create, name='position_create'),
    path('add/', views.add_position, name='add_position'),
    path('active/', views.active_positions, name='active_positions'),
    path('<int:position_id>/overview/', views.position_overview, name='position_overview'),
    path('<int:position_id>/add-candidate/', views.add_candidate_to_position, name='add_candidate_to_position'),
] 