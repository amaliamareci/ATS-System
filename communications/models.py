from django.db import models
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

# Create your models here.

class Comment(models.Model):
    process = models.ForeignKey('recruitment.RecruitingProcess', on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.author} on {self.process}'

class RejectionEmail(models.Model):
    recruiting_process = models.ForeignKey('recruitment.RecruitingProcess', on_delete=models.CASCADE)
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
