from django.db import models

# Create your models here.

class Meeting(models.Model):
    MEETING_TYPES = [
        ('phone_screen', 'Phone Screen'),
        ('technical', 'Technical Interview'),
        ('hr', 'HR Interview'),
        ('client', 'Client Interview'),
        ('final', 'Final Interview'),
    ]
    
    recruiting_process = models.ForeignKey('recruitment.RecruitingProcess', on_delete=models.CASCADE, related_name='meetings')
    recruiter = models.ForeignKey('recruiters.Recruiter', on_delete=models.CASCADE)
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPES)
    date_time = models.DateTimeField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_time']

    def __str__(self):
        return f"{self.get_meeting_type_display()} with {self.recruiting_process.candidate.first_name} {self.recruiting_process.candidate.last_name}"
