from django.urls import path
from . import views

app_name = 'communications'

urlpatterns = [
    path('process/<int:process_id>/add-comment/', views.add_comment, name='add_comment'),
    path('process/<int:process_id>/delete-comment/<int:comment_id>/', views.delete_comment, name='delete_comment'),
    path('process/<int:process_id>/schedule-rejection-email/', views.schedule_rejection_email, name='schedule_rejection_email'),
] 