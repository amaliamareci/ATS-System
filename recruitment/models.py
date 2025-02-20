from django.db import models

# Create your models here.

class PipelineStage(models.Model):
    """Defines a stage in a client's recruitment pipeline"""
    client = models.ForeignKey('clients.Client', on_delete=models.CASCADE, related_name='pipeline_stages')
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
    candidate = models.ForeignKey('candidates.Candidate', on_delete=models.CASCADE)
    position = models.ForeignKey('positions.Position', on_delete=models.CASCADE)
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
