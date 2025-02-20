from django.db import models
from recruitment.models import PipelineStage, PipelineSubStatus

# Create your models here.

class Client(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            self.create_default_pipeline_stages()

    def create_default_pipeline_stages(self):
        """Creates default hiring stages and sub-statuses"""
        default_stages = [
            {
                'key': 'pending_screening',
                'name': 'Pending Screening',
                'order': 1,
                'color': '#374151',  # Darker gray
                'sub_statuses': [
                    ('screening_not_created', 'Screening Not Created', 1),
                    ('screening_created', 'Screening Created', 2),
                ]
            },
            {
                'key': 'screening',
                'name': 'Screening',
                'order': 2,
                'color': '#1D4ED8',  # Darker blue
                'sub_statuses': [
                    ('unscreened', 'Unscreened', 1),
                    ('screening_scheduled', 'Screening Scheduled', 2),
                    ('can_be_sent', 'Can be sent to client', 3),
                    ('rejected', 'Rejected', 4),
                    ('junk_candidate', 'Junk candidate', 5),
                    ('absent', 'Absent', 6),
                    ('on_hold', 'On Hold', 7),
                ]
            },
            {
                'key': 'validation',
                'name': 'Validation at Client',
                'order': 3,
                'color': '#5B21B6',  # Darker purple
                'sub_statuses': [
                    ('under_review', 'Under Review', 1),
                    ('approved_by_client', 'Approved by client', 2),
                    ('rejected_by_client', 'Rejected by client', 3),
                ]
            },
            {
                'key': 'client_interview',
                'name': 'Client Interview',
                'order': 4,
                'color': '#B45309',  # Darker amber
                'sub_statuses': [
                    ('to_be_scheduled', 'To be scheduled', 1),
                    ('interview_scheduled', 'Interview Scheduled', 2),
                    ('approved_by_client', 'Approved by client', 3),
                    ('rejected_by_client', 'Rejected by client', 4),
                ]
            },
            {
                'key': 'offered',
                'name': 'Offered',
                'order': 5,
                'color': '#047857',  # Darker green
                'sub_statuses': [
                    ('offer_made', 'Offer made', 1),
                    ('offer_accepted', 'Offer accepted', 2),
                    ('offer_declined', 'Offer declined', 3),
                ]
            },
            {
                'key': 'rejected',
                'name': 'Rejected',
                'order': 6,
                'color': '#B91C1C',  # Darker red
                'sub_statuses': [
                    ('rejected_screening', 'Rejected from Screening', 1),
                    ('junk_screening', 'Junk candidate from Screening', 2),
                    ('rejected_validation', 'Rejected by client from Validation', 3),
                    ('rejected_interview', 'Rejected by client from Interview', 4),
                    ('offer_declined', 'Offer declined', 5),
                ]
            },
        ]
        
        for stage_data in default_stages:
            stage = PipelineStage.objects.create(
                client=self,
                key=stage_data['key'],
                name=stage_data['name'],
                order=stage_data['order'],
                color=stage_data['color']
            )
            
            for sub_status_key, sub_status_name, sub_status_order in stage_data['sub_statuses']:
                PipelineSubStatus.objects.create(
                    stage=stage,
                    key=sub_status_key,
                    name=sub_status_name,
                    order=sub_status_order
                )
