from django.contrib import admin
from .models import (
    AssessmentTemplate,
    CompetencyArea,
    AssessmentQuestion,
    CandidateAssessment,
    QuestionResponse,
    CompetencyScore
)

@admin.register(AssessmentTemplate)
class AssessmentTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('is_active',)

@admin.register(CompetencyArea)
class CompetencyAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    search_fields = ('name',)
    ordering = ('order',)

@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'competency_area', 'template', 'order')
    list_filter = ('competency_area', 'template')
    search_fields = ('question_text',)
    ordering = ('competency_area__order', 'order')

@admin.register(CandidateAssessment)
class CandidateAssessmentAdmin(admin.ModelAdmin):
    list_display = ('recruiting_process', 'overall_rating', 'job_match_percentage', 'is_completed', 'created_by')
    list_filter = ('completed_at', 'created_at')
    search_fields = ('recruiting_process__candidate__first_name', 'recruiting_process__candidate__last_name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(QuestionResponse)
class QuestionResponseAdmin(admin.ModelAdmin):
    list_display = ('assessment', 'question', 'rating')
    list_filter = ('assessment__template', 'question__competency_area')
    search_fields = ('response_text',)

@admin.register(CompetencyScore)
class CompetencyScoreAdmin(admin.ModelAdmin):
    list_display = ('assessment', 'competency_area', 'score')
    list_filter = ('competency_area',)
    search_fields = ('assessment__recruiting_process__candidate__first_name', 'assessment__recruiting_process__candidate__last_name')
