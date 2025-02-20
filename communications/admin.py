from django.contrib import admin
from .models import Comment, RejectionEmail

# Register your models here.
admin.site.register(Comment)
admin.site.register(RejectionEmail)
