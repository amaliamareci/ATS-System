from django.urls import path
from . import views

app_name = 'recruiters'

urlpatterns = [
    path('', views.recruiter_list, name='recruiter_list'),
    path('create/', views.recruiter_create, name='recruiter_create'),
] 