from django.db import models
from django.core.validators import FileExtensionValidator

# Create your models here.

class Competency(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    class Meta:
        verbose_name_plural = "Competencies"
        
    def __str__(self):
        return self.name

class Language(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name

class Candidate(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    source = models.CharField(max_length=20, choices=[
        ('LinkedIn', 'LinkedIn'),
        ('Jobs', 'Jobs'),
        ('Internal', 'Internal')
    ], default='LinkedIn')
    resume = models.FileField(
        upload_to='resumes/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])],
        null=True,
        blank=True,
        help_text='Allowed formats: PDF, DOC, DOCX'
    )
    consultant = models.ForeignKey('recruiters.Recruiter', on_delete=models.SET_NULL, null=True, blank=True, related_name='candidates')
    competencies = models.ManyToManyField(Competency, blank=True)
    languages = models.ManyToManyField(Language, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('new', 'New'),
        ('screening', 'Screening'),
        ('interviewing', 'Interviewing'),
        ('offered', 'Offered'),
        ('hired', 'Hired'),
        ('rejected', 'Rejected')
    ], default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_active_positions(self):
        """Get all positions the candidate is currently in process for"""
        return Position.objects.filter(recruitingprocess__candidate=self).distinct()

    def get_current_process(self, position):
        """Get the current recruiting process for a specific position"""
        return self.recruitingprocess_set.filter(position=position).first()
