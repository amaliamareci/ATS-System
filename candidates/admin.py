from django.contrib import admin
from .models import Candidate, Competency, Language

admin.site.register(Candidate)
admin.site.register(Competency)
admin.site.register(Language)
