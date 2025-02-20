from django.contrib import admin
from .models import RecruitingProcess, PipelineStage, PipelineSubStatus, StatusChange

admin.site.register(RecruitingProcess)
admin.site.register(PipelineStage)
admin.site.register(PipelineSubStatus)
admin.site.register(StatusChange)
