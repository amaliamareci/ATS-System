from django.contrib import admin
from .models import Client, Position, Candidate, Meeting

admin.site.register(Client)
admin.site.register(Position)
admin.site.register(Candidate)
admin.site.register(Meeting)
