from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from core.models import RejectionEmail

class Command(BaseCommand):
    help = 'Sends scheduled rejection emails'

    def handle(self, *args, **options):
        now = timezone.now()
        pending_emails = RejectionEmail.objects.filter(
            scheduled_time__lte=now,
            sent_at__isnull=True
        )

        for email in pending_emails:
            process = email.recruiting_process
            try:
                send_mail(
                    subject=f'Application Update for {process.position.title}',
                    message=email.email_content,
                    from_email=None,  # Uses DEFAULT_FROM_EMAIL
                    recipient_list=[process.candidate.email],
                )
                email.sent_at = now
                email.save()
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully sent rejection email to {process.candidate.email}'
                ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'Failed to send email to {process.candidate.email}: {str(e)}'
                )) 