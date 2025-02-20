from django.db import models

# Create your models here.

class Recruiter(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    role = models.CharField(max_length=50, choices=[
        ('recruiter', 'Recruiter'),
        ('technical', 'Technical Interviewer'),
        ('hr', 'HR Manager'),
        ('manager', 'Hiring Manager')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"
