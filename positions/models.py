from django.db import models

# Create your models here.

class Position(models.Model):
    STATUS_CHOICES = [
        ('open', 'Active'),
        ('closed', 'Closed'),
        ('hold', 'On Hold')
    ]
    
    title = models.CharField(max_length=200)
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, related_name='positions')
    description = models.TextField()
    requirements = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    candidates = models.ManyToManyField('candidates.Candidate', through='recruitment.RecruitingProcess', related_name='positions')

    def __str__(self):
        return f"{self.title} - {self.client.name}"

    def get_candidates_by_status(self, status):
        """Get all candidates for this position with a specific status"""
        return self.candidates.filter(recruitingprocess__status=status)

    def get_active_candidates(self):
        """Get all candidates currently in process"""
        return self.candidates.exclude(recruitingprocess__status__in=['refused', 'accepted'])

    def get_in_process_count(self):
        return self.recruitingprocess_set.exclude(
            stage__key__in=['offered', 'rejected']
        ).count()

    def get_hired_count(self):
        return self.recruitingprocess_set.filter(
            stage__key='offered'
        ).count()

    @property
    def open_positions(self):
        # For now, return a fixed number or calculate based on your business logic
        return 1  # or any other calculation you need

    @property
    def in_process(self):
        return RecruitingProcess.objects.filter(
            candidate__positions=self,
            status__in=['phone_interview', 'validation', 'client_interview']
        ).count()
