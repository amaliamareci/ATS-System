from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    path('process/<int:process_id>/', views.assessment_detail, name='assessment_detail'),
    path('process/<int:process_id>/report/', views.assessment_report, name='assessment_report'),
] 