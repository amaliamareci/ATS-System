from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.core.validators import FileExtensionValidator

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

class Position(models.Model):
    STATUS_CHOICES = [
        ('open', 'Active'),
        ('closed', 'Closed'),
        ('hold', 'On Hold')
    ]
    
    title = models.CharField(max_length=200)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='positions')
    description = models.TextField()
    requirements = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    candidates = models.ManyToManyField('Candidate', through='RecruitingProcess', related_name='positions')

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
    consultant = models.ForeignKey('Recruiter', on_delete=models.SET_NULL, null=True, blank=True, related_name='candidates')
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

class PipelineStage(models.Model):
    """Defines a stage in a client's recruitment pipeline"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='pipeline_stages')
    key = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField()
    color = models.CharField(max_length=20, default='#3B82F6')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        unique_together = ['client', 'key']

    def __str__(self):
        return f"{self.client.name} - {self.name}"

class PipelineSubStatus(models.Model):
    """Defines possible sub-statuses within a pipeline stage"""
    stage = models.ForeignKey(PipelineStage, on_delete=models.CASCADE, related_name='sub_statuses')
    key = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField()
    
    class Meta:
        ordering = ['order']
        unique_together = ['stage', 'key']

    def __str__(self):
        return f"{self.stage.name} - {self.name}"

class RecruitingProcess(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    stage = models.ForeignKey(PipelineStage, on_delete=models.CASCADE)
    sub_status = models.ForeignKey(PipelineSubStatus, on_delete=models.CASCADE)
    interview_score = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True, help_text='Interview score out of 10')
    cv_match = models.IntegerField(null=True, blank=True, help_text='CV match percentage')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # If this is a new process (no ID yet)
        if not self.pk:
            # Get the first stage and sub-status for the client if not set
            if not self.stage:
                self.stage = self.position.client.pipeline_stages.order_by('order').first()
            if not self.sub_status and self.stage:
                self.sub_status = self.stage.sub_statuses.order_by('order').first()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.candidate} - {self.position}"

class StatusChange(models.Model):
    process = models.ForeignKey(RecruitingProcess, on_delete=models.CASCADE, related_name='status_changes')
    old_stage = models.ForeignKey(PipelineStage, on_delete=models.SET_NULL, null=True, blank=True, related_name='old_status_changes')
    new_stage = models.ForeignKey(PipelineStage, on_delete=models.CASCADE, related_name='new_status_changes')
    old_sub_status = models.ForeignKey(PipelineSubStatus, on_delete=models.SET_NULL, null=True, blank=True, related_name='old_status_changes')
    new_sub_status = models.ForeignKey(PipelineSubStatus, on_delete=models.CASCADE, related_name='new_status_changes')
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        if self.old_stage:
            return f"Changed from {self.old_stage.name} ({self.old_sub_status.name}) to {self.new_stage.name} ({self.new_sub_status.name})"
        return f"Initial status: {self.new_stage.name} ({self.new_sub_status.name})"

class Meeting(models.Model):
    MEETING_TYPES = [
        ('phone_screen', 'Phone Screen'),
        ('technical', 'Technical Interview'),
        ('hr', 'HR Interview'),
        ('client', 'Client Interview'),
        ('final', 'Final Interview'),
    ]
    
    recruiting_process = models.ForeignKey(RecruitingProcess, on_delete=models.CASCADE, related_name='meetings')
    recruiter = models.ForeignKey(Recruiter, on_delete=models.CASCADE)
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPES)
    date_time = models.DateTimeField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_time']

    def __str__(self):
        return f"{self.get_meeting_type_display()} with {self.recruiting_process.candidate.first_name} {self.recruiting_process.candidate.last_name}"

class RejectionEmail(models.Model):
    recruiting_process = models.ForeignKey(RecruitingProcess, on_delete=models.CASCADE)
    scheduled_date = models.DateTimeField()
    email_subject = models.CharField(max_length=200, default="Application Status Update")
    email_body = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('failed', 'Failed')
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    def send_email(self):
        try:
            send_mail(
                subject=self.email_subject,
                message=self.email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.recruiting_process.candidate.email],
                fail_silently=False,
            )
            self.status = 'sent'
            self.sent_at = timezone.now()
            self.save()
            return True
        except Exception as e:
            self.status = 'failed'
            self.save()
            return False

    def __str__(self):
        return f"Rejection Email for {self.recruiting_process.candidate} - {self.status}"

class Comment(models.Model):
    process = models.ForeignKey(RecruitingProcess, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.author} on {self.process}'
