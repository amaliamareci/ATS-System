from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Comment, RejectionEmail
from recruitment.models import RecruitingProcess
from django.utils import timezone
import json

# Create your views here.

@login_required
def add_comment(request, process_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    process = get_object_or_404(RecruitingProcess, pk=process_id)
    content = request.POST.get('content')
    
    if not content:
        return JsonResponse({'error': 'Comment content is required'}, status=400)
    
    comment = Comment.objects.create(
        process=process,
        author=request.user,
        content=content
    )
    
    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'author': f"{comment.author.first_name} {comment.author.last_name}",
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    })

@login_required
def delete_comment(request, process_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id, process_id=process_id)
    
    # Only allow the author to delete their own comments
    if comment.author != request.user:
        return JsonResponse({'error': 'Not authorized to delete this comment'}, status=403)
    
    comment.delete()
    return JsonResponse({'success': True})

@login_required
def schedule_rejection_email(request, process_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    process = get_object_or_404(RecruitingProcess, pk=process_id)
    
    try:
        data = json.loads(request.body)
        scheduled_date = data.get('scheduled_date')
        email_subject = data.get('email_subject')
        email_body = data.get('email_body')
        
        if not all([scheduled_date, email_subject, email_body]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        rejection_email = RejectionEmail.objects.create(
            recruiting_process=process,
            scheduled_date=scheduled_date,
            email_subject=email_subject,
            email_body=email_body
        )
        
        return JsonResponse({
            'success': True,
            'email': {
                'id': rejection_email.id,
                'scheduled_date': rejection_email.scheduled_date.strftime('%Y-%m-%d %H:%M:%S'),
                'status': rejection_email.status
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
