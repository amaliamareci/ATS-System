from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User

class AssessmentTemplate(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class CompetencyArea(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name

class AssessmentQuestion(models.Model):
    template = models.ForeignKey(AssessmentTemplate, on_delete=models.CASCADE, related_name='questions')
    competency_area = models.ForeignKey(CompetencyArea, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['competency_area__order', 'order']

    def __str__(self):
        return f"{self.competency_area.name}: {self.question_text[:50]}..."

class CandidateAssessment(models.Model):
    recruiting_process = models.OneToOneField('recruitment.RecruitingProcess', on_delete=models.CASCADE, related_name='assessment')
    template = models.ForeignKey(AssessmentTemplate, on_delete=models.PROTECT)
    overall_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        null=True,
        blank=True
    )
    job_match_percentage = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    key_strengths = models.ManyToManyField('candidates.Competency', blank=True)
    final_recommendation = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_assessments')
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='updated_assessments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Assessment for {self.recruiting_process}"

    @property
    def is_completed(self):
        return bool(self.completed_at)

class QuestionResponse(models.Model):
    assessment = models.ForeignKey(CandidateAssessment, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(AssessmentQuestion, on_delete=models.PROTECT)
    response_text = models.TextField()
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['assessment', 'question']

    def __str__(self):
        return f"Response to {self.question} for {self.assessment}"

class CompetencyScore(models.Model):
    assessment = models.ForeignKey(CandidateAssessment, on_delete=models.CASCADE, related_name='competency_scores')
    competency_area = models.ForeignKey(CompetencyArea, on_delete=models.PROTECT)
    score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['assessment', 'competency_area']

    def __str__(self):
        return f"{self.competency_area.name}: {self.score}/10"
