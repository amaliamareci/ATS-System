from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from candidates.models import Candidate, Competency, Language
from positions.models import Position
from clients.models import Client
from meetings.models import Meeting
from recruiters.models import Recruiter
from recruitment.models import RecruitingProcess, PipelineStage, PipelineSubStatus, StatusChange
from communications.models import RejectionEmail, Comment
from .forms import CandidateForm, PositionForm, ClientForm, MeetingForm, RecruiterForm, RecruitingProcessForm
from datetime import datetime, timedelta
from django.utils import timezone
from calendar import monthrange
from django.db import models
from django.http import Http404, JsonResponse, HttpResponse
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
import os
import json
from django.db.models import Q, Value, FloatField, Avg, Count, F
from django.db.models.functions import Cast, Extract
import re
import PyPDF2
import docx
import io
import fitz  # PyMuPDF
import tempfile
import openai
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, Q, Subquery, OuterRef

# Create your views here.

def candidate_list(request):
    candidates = Candidate.objects.all().order_by('-created_at')
    return render(request, 'core/candidate_list.html', {'candidates': candidates})

def position_list(request):
    positions = Position.objects.all().order_by('-created_at')
    return render(request, 'core/position_list.html', {'positions': positions})

def validate_file_size(value):
    filesize = value.size
    
    if filesize > 10 * 1024 * 1024:  # 10MB limit
        raise ValidationError("The maximum file size that can be uploaded is 10MB")
    return value

def candidate_create(request):
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                if 'resume' in request.FILES:
                    resume = request.FILES['resume']
                    validate_file_size(resume)
                    
                    # Sanitize filename
                    filename = resume.name
                    filename = ''.join(c for c in filename if c.isalnum() or c in ('-', '_', '.'))
                    resume.name = filename
                    
                candidate = form.save()
                return redirect('candidate_list')
            except ValidationError as e:
                form.add_error('resume', e.message)
        else:
            print(f"Form errors: {form.errors}")  # For debugging
    else:
        form = CandidateForm()
    return render(request, 'core/candidate_form.html', {'form': form})

def position_create(request):
    # Get position ID from query parameters for editing
    position_id = request.GET.get('id')
    position = None
    if position_id:
        position = get_object_or_404(Position, id=position_id)

    if request.method == 'POST':
        form = PositionForm(request.POST, instance=position)
        if form.is_valid():
            form.save()
            return redirect('position_list')
    else:
        form = PositionForm(instance=position)
    
    context = {
        'form': form,
        'is_edit': position is not None,
        'title': 'Edit Position' if position else 'Create Position'
    }
    return render(request, 'core/position_form.html', context)

@login_required
def client_list(request):
    clients = Client.objects.all().prefetch_related(
        'positions',
        'positions__recruitingprocess_set'
    ).order_by('name')
    return render(request, 'core/client_list.html', {'clients': clients})

@login_required
def add_client(request):
    if request.method == 'POST':
        try:
            client = Client.objects.create(
                name=request.POST['name'],
                email=request.POST['email'],
                phone=request.POST['phone']
            )
            return JsonResponse({'success': True, 'client_id': client.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def edit_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method == 'POST':
        try:
            client.name = request.POST['name']
            client.email = request.POST['email']
            client.phone = request.POST['phone']
            client.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def delete_client(request, client_id):
    if request.method == 'POST':
        try:
            client = get_object_or_404(Client, id=client_id)
            client.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def add_position(request):
    if request.method == 'POST':
        try:
            client = get_object_or_404(Client, id=request.POST['client_id'])
            position = Position.objects.create(
                client=client,
                title=request.POST['title'],
                description=request.POST['description'],
                requirements=request.POST['requirements']
            )
            return JsonResponse({'success': True, 'position_id': position.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def meeting_list(request):
    meetings = Meeting.objects.all().order_by('-date_time')
    return render(request, 'core/meeting_list.html', {'meetings': meetings})

def meeting_create(request):
    if request.method == 'POST':
        form = MeetingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('meeting_list')
    else:
        form = MeetingForm()
    return render(request, 'core/meeting_form.html', {'form': form})

def recruiter_list(request):
    recruiters = Recruiter.objects.all().order_by('first_name', 'last_name')
    return render(request, 'core/recruiter_list.html', {'recruiters': recruiters})

def recruiter_create(request):
    # Get recruiter ID from query parameters for editing
    recruiter_id = request.GET.get('id')
    recruiter = None
    if recruiter_id:
        recruiter = get_object_or_404(Recruiter, id=recruiter_id)

    if request.method == 'POST':
        form = RecruiterForm(request.POST, instance=recruiter)
        if form.is_valid():
            form.save()
            return redirect('recruiter_list')
    else:
        form = RecruiterForm(instance=recruiter)
    
    context = {
        'form': form,
        'is_edit': recruiter is not None,
        'title': 'Edit Recruiter' if recruiter else 'Create Recruiter'
    }
    return render(request, 'core/recruiter_form.html', context)

def meeting_calendar(request):
    # Get selected recruiter from query params, default to 'all'
    selected_recruiter_id = request.GET.get('recruiter', 'all')
    
    # Get all recruiters for the filter
    recruiters = Recruiter.objects.all().order_by('first_name', 'last_name')
    
    # Get current date info
    today = timezone.now()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
    # Get all days in the month
    _, num_days = monthrange(year, month)
    first_day = datetime(year, month, 1)
    days = [(first_day + timedelta(days=d)).date() for d in range(num_days)]
    
    # Get meetings for the month
    meetings = Meeting.objects.filter(
        date_time__year=year,
        date_time__month=month
    ).order_by('date_time')
    
    # Filter by recruiter if specified
    if selected_recruiter_id != 'all':
        meetings = meetings.filter(recruiter_id=selected_recruiter_id)
    
    # Organize meetings by date
    meetings_by_date = {}
    for meeting in meetings:
        date = meeting.date_time.date()
        if date not in meetings_by_date:
            meetings_by_date[date] = []
        meetings_by_date[date].append(meeting)
    
    context = {
        'recruiters': recruiters,
        'selected_recruiter_id': selected_recruiter_id,
        'days': days,
        'meetings_by_date': meetings_by_date,
        'year': year,
        'month': month,
        'month_name': first_day.strftime('%B'),
        'prev_month': (first_day - timedelta(days=1)).strftime('%Y-%m'),
        'next_month': (first_day + timedelta(days=32)).strftime('%Y-%m'),
        'today': today.date(),
    }
    return render(request, 'core/meeting_calendar.html', context)

@login_required
def active_positions(request):
    # Get all clients with their positions
    clients = Client.objects.prefetch_related(
        'positions',
        'positions__recruitingprocess_set',
        'positions__recruitingprocess_set__candidate',
        'positions__recruitingprocess_set__candidate__consultant'
    ).all()

    print("Debug: Starting position processing")  # Debug print

    # Calculate total open positions
    total_open_positions = Position.objects.filter(status='open').count()
    print(f"Debug: Found {total_open_positions} open positions")  # Debug print

    # Process each client's positions
    for client in clients:
        print(f"\nDebug: Processing client: {client.name}")  # Debug print
        
        # Filter active positions for this client
        client.active_positions = client.positions.filter(status='open').annotate(
            in_process_count=Count(
                'recruitingprocess',
                filter=~Q(recruitingprocess__stage__key__in=['offered', 'rejected'])
            ),
            hired_count=Count(
                'recruitingprocess',
                filter=Q(recruitingprocess__stage__key='offered')
            ),
            candidate_count=Count('recruitingprocess', distinct=True)
        )

        # Get consultants for each position
        for position in client.active_positions:
            print(f"\nDebug: Processing position: {position.title}")  # Debug print
            
            # Get recruiting processes for this position
            recruiting_processes = position.recruitingprocess_set.select_related(
                'candidate',
                'candidate__consultant'
            ).all()
            
            print(f"Debug: Found {recruiting_processes.count()} recruiting processes")  # Debug print
            
            # Get unique consultants from candidates
            consultants = []
            for rp in recruiting_processes:
                print(f"Debug: Processing recruiting process {rp.id}")  # Debug print
                if rp.candidate:
                    print(f"Debug: Found candidate: {rp.candidate.first_name} {rp.candidate.last_name}")  # Debug print
                    if rp.candidate.consultant:
                        consultant = rp.candidate.consultant
                        print(f"Debug: Found consultant: {consultant.first_name} {consultant.last_name}")  # Debug print
                        if consultant not in consultants:
                            consultants.append(consultant)
                            print(f"Debug: Added consultant to list")  # Debug print
            
            position.consultants = consultants
            position.consultant_count = len(consultants)
            print(f"Debug: Position has {len(consultants)} consultants")  # Debug print

    context = {
        'clients': clients,
        'total_open_positions': total_open_positions,
    }
    
    return render(request, 'core/active_positions.html', context)

def candidate_edit(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            form.save()
            return redirect('candidate_list')
    else:
        form = CandidateForm(instance=candidate)
    return render(request, 'core/candidate_form.html', {'form': form})

@login_required
def recruiting_process_list(request):
    processes = RecruitingProcess.objects.all().select_related(
        'candidate', 'position', 'position__client', 'stage', 'sub_status'
    ).prefetch_related('candidate__consultant')

    # Initialize dictionary with all possible stages
    processes_by_stage = {
        'pending_screening': [],
        'screening': [],
        'validation': [],
        'client_interview': [],
        'offered': [],
        'rejected': [],
    }

    # Categorize processes by stage
    for process in processes:
        stage_key = process.stage.key
        if stage_key not in processes_by_stage:
            processes_by_stage['pending_screening'].append(process)  # Default to pending_screening if unknown
        else:
            processes_by_stage[stage_key].append(process)

    return render(request, 'core/recruiting_process_list.html', {
        'processes': processes,
        'processes_by_stage': processes_by_stage,
        'stage_names': {  # Add friendly names for the stages
            'pending_screening': 'Pending Screening',
            'screening': 'Screening',
            'validation': 'Validation',
            'client_interview': 'Client Interview',
            'offered': 'Offered',
            'rejected': 'Rejected',
        }
    })

@login_required
def recruiting_process_create(request):
    if request.method == 'POST':
        form = RecruitingProcessForm(request.POST)
        if form.is_valid():
            process = form.save(commit=False)
            # Get the first stage and sub-status for the client
            first_stage = process.position.client.pipeline_stages.order_by('order').first()
            if first_stage:
                first_sub_status = first_stage.sub_statuses.order_by('order').first()
                process.stage = first_stage
                process.sub_status = first_sub_status
                process.save()
                return redirect('recruiting_process_list')
    else:
        # Get position_id from query parameters if it exists
        position_id = request.GET.get('position')
        initial_data = {}
        if position_id:
            try:
                position = Position.objects.get(id=position_id)
                initial_data['position'] = position
            except Position.DoesNotExist:
                pass
        form = RecruitingProcessForm(initial=initial_data)

    return render(request, 'core/recruiting_process_form.html', {
        'form': form,
        'title': 'Add Recruiting Process'
    })

def recruiting_process_edit(request, pk):
    process = get_object_or_404(RecruitingProcess, pk=pk)
    if request.method == 'POST':
        form = RecruitingProcessForm(request.POST, instance=process)
        if form.is_valid():
            form.save()
            return redirect('recruiting_process_list')
    else:
        form = RecruitingProcessForm(instance=process)
    
    return render(request, 'core/recruiting_process_form.html', {
        'form': form,
        'title': 'Edit Recruiting Process'
    })

@login_required
def position_recruiting_process(request, position_id):
    position = get_object_or_404(Position.objects.select_related('client'), id=position_id)
    
    # Get all processes for this position
    processes = RecruitingProcess.objects.filter(
        position=position
    ).select_related(
        'candidate', 'stage', 'sub_status'
    ).prefetch_related(
        'candidate__competencies',
        'candidate__languages'
    )
    
    # Group processes by stage
    pipeline_data = []
    stages = position.client.pipeline_stages.all().prefetch_related('sub_statuses')
    
    # Calculate total candidates
    total_candidates = processes.count()
    
    for stage in stages:
        stage_processes = processes.filter(stage=stage)
        sub_status_groups = {}
        
        # Group by sub-status
        for process in stage_processes:
            if process.sub_status not in sub_status_groups:
                sub_status_groups[process.sub_status] = []
            
            # Calculate days in stage
            days_in_stage = (timezone.now().date() - process.created_at.date()).days
            
            # Get candidate source (LinkedIn, Jobs, Internal)
            source = process.candidate.source if hasattr(process.candidate, 'source') else "LinkedIn"
            
            sub_status_groups[process.sub_status].append({
                'id': process.id,
                'candidate': {
                    'id': process.candidate.id,
                    'first_name': process.candidate.first_name,
                    'last_name': process.candidate.last_name,
                },
                'days_in_stage': days_in_stage,
                'source': source,
                'interview_score': float(process.interview_score) if process.interview_score else None,
                'cv_match': process.cv_match
            })
        
        # Sort sub-statuses by their order
        sorted_sub_statuses = stage.sub_statuses.all().order_by('order')
        
        stage_data = {
            'key': stage.key,
            'name': stage.name,
            'color': stage.color,
            'total_count': stage_processes.count(),
            'sub_statuses': []
        }
        
        # Add each sub-status with its processes
        for sub_status in sorted_sub_statuses:
            processes_list = sub_status_groups.get(sub_status, [])
            stage_data['sub_statuses'].append({
                'key': sub_status.key,
                'name': sub_status.name,
                'processes': processes_list
            })
        
        pipeline_data.append(stage_data)

    # Serialize pipeline data to JSON
    pipeline_data_json = json.dumps(pipeline_data, cls=DjangoJSONEncoder)

    context = {
        'position': position,
        'pipeline_data': pipeline_data,
        'pipeline_data_json': pipeline_data_json,
        'total_candidates': total_candidates,  # Add total_candidates to context
    }
    return render(request, 'core/position_pipeline.html', context)

@login_required
def position_overview(request, position_id):
    position = get_object_or_404(Position.objects.select_related('client'), id=position_id)
    
    # Get all processes for this position
    processes = RecruitingProcess.objects.filter(
        position=position
    ).select_related(
        'candidate', 'stage', 'sub_status'
    )
    
    # Calculate metrics
    total_candidates = processes.count()
    active_candidates = processes.exclude(stage__key__in=['offered', 'rejected']).count()
    
    # Hardcoded consultant info for now
    consultant_info = {
        'name': 'John Smith',
        'email': 'john.smith@company.com',
        'phone': '+1 (555) 123-4567'
    }
    
    # Hardcoded hiring process stages
    hiring_stages = [
        {'name': 'Initial Screening', 'duration': '1-2 days'},
        {'name': 'Technical Assessment', 'duration': '3-5 days'},
        {'name': 'First Interview', 'duration': '1 day'},
        {'name': 'Second Interview', 'duration': '1 day'},
        {'name': 'Final Decision', 'duration': '2-3 days'}
    ]
    
    context = {
        'position': position,
        'total_candidates': total_candidates,
        'active_candidates': active_candidates,
        'consultant': consultant_info,
        'hiring_stages': hiring_stages,
    }
    
    return render(request, 'core/position_overview.html', context)

@login_required
def delete_comment(request, process_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, process_id=process_id)
    
    # Check if the user is the author of the comment
    if comment.author != request.user:
        return JsonResponse({
            'success': False,
            'error': 'You can only delete your own comments'
        }, status=403)
    
    try:
        comment.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def add_comment(request, process_id):
    # Check authentication
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")
    
    process = get_object_or_404(RecruitingProcess, id=process_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            comment = Comment.objects.create(
                process=process,
                author=request.user,
                content=content
            )
            return JsonResponse({
                'success': True,
                'author_name': request.user.get_full_name() or request.user.username,
                'comment_id': comment.id
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def schedule_meeting(request, process_id):
    process = get_object_or_404(RecruitingProcess, id=process_id)
    
    if request.method == 'POST':
        try:
            meeting_type = request.POST.get('meeting_type')
            date_time_str = request.POST.get('date_time')
            notes = request.POST.get('notes', '')
            
            # Convert the date_time string to a datetime object
            date_time = datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M')
            
            # Use the candidate's consultant as the recruiter for the meeting
            recruiter = process.candidate.consultant
            if not recruiter:
                return JsonResponse({
                    'success': False,
                    'error': 'No consultant assigned to this candidate'
                })

            meeting = Meeting.objects.create(
                recruiting_process=process,
                recruiter=recruiter,
                meeting_type=meeting_type,
                date_time=date_time,
                notes=notes
            )

            return JsonResponse({
                'success': True,
                'meeting': {
                    'type': meeting.get_meeting_type_display(),
                    'date_time': meeting.date_time.strftime('%B %d, %Y, %I:%M %p'),
                    'recruiter': f"{meeting.recruiter.first_name} {meeting.recruiter.last_name}",
                    'notes': meeting.notes
                }
            })
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': 'Invalid date format'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

@login_required
def candidate_recruiting_process(request, position_id, candidate_id):
    position = get_object_or_404(Position, id=position_id)
    candidate = get_object_or_404(Candidate, id=candidate_id)
    process = get_object_or_404(RecruitingProcess, 
        candidate=candidate,
        position=position
    )
    
    if request.method == 'POST':
        # Handle stage/sub-status update
        new_stage_id = request.POST.get('stage')
        new_sub_status_id = request.POST.get('sub_status')
        
        if new_stage_id and new_sub_status_id:
            old_stage = process.stage
            old_sub_status = process.sub_status
            
            # Update process with new stage and sub-status
            process.stage = get_object_or_404(PipelineStage, id=new_stage_id)
            process.sub_status = get_object_or_404(PipelineSubStatus, id=new_sub_status_id)
            process.save()
            
            # Record the status change
            StatusChange.objects.create(
                process=process,
                old_stage=old_stage,
                new_stage=process.stage,
                old_sub_status=old_sub_status,
                new_sub_status=process.sub_status
            )
        
        if request.headers.get('HX-Request'):
            return redirect('position_recruiting_process', position_id=process.position.id)
        return redirect('position_recruiting_process', position_id=process.position.id)
    
    # Get all meetings for this process with recruiter data
    meetings = Meeting.objects.filter(recruiting_process=process).select_related('recruiter').order_by('-date_time')
    
    # Get comments for this process
    comments = process.comments.select_related('author').all()
    
    # Get the rejection email template to the context
    rejection_email_template = get_rejection_email_template(process)
    
    # Get all pipeline stages and sub-statuses for the client
    pipeline_stages = position.client.pipeline_stages.prefetch_related('sub_statuses').all()
    
    # Ensure stages are ordered correctly
    if not pipeline_stages.exists():
        # If no stages exist, create default stages
        position.client.create_default_pipeline_stages()
        pipeline_stages = position.client.pipeline_stages.prefetch_related('sub_statuses').all()
    
    # Get next possible sub-statuses
    current_stage = process.stage
    current_sub_status = process.sub_status
    next_sub_statuses = []
    
    # Get the current stage index (1-based)
    pipeline_stages = list(pipeline_stages)  # Convert to list for index operations
    current_stage_index = pipeline_stages.index(current_stage) + 1
    
    # Get sub-statuses from current stage that come after current sub-status
    current_stage_sub_statuses = list(current_stage.sub_statuses.all().order_by('order'))
    current_index = next((i for i, s in enumerate(current_stage_sub_statuses) if s.id == current_sub_status.id), -1)
    
    # Add remaining sub-statuses from current stage
    if current_index >= 0:
        next_sub_statuses.extend(current_stage_sub_statuses[current_index + 1:])
    
    # If we're at the last sub-status of the current stage or there are no next sub-statuses in current stage,
    # get the first sub-status of the next stage
    if current_index == len(current_stage_sub_statuses) - 1 or not next_sub_statuses:
        # Get next stage by index rather than order field
        current_stage_idx = pipeline_stages.index(current_stage)
        if current_stage_idx < len(pipeline_stages) - 1:
            next_stage = pipeline_stages[current_stage_idx + 1]
            next_stage_sub_statuses = list(next_stage.sub_statuses.all().order_by('order'))
            if next_stage_sub_statuses:
                next_sub_statuses.extend(next_stage_sub_statuses)
    
    # Debug information
    print("Pipeline stages:", [(s.name, s.order) for s in pipeline_stages])
    print("Current stage:", current_stage.name, current_stage.order)
    print("Current sub-status:", current_sub_status.name)
    print("Next sub-statuses:", [f"{s.name} ({s.stage.name})" for s in next_sub_statuses])
    
    context = {
        'position': position,
        'candidate': candidate,
        'process': process,
        'meetings': meetings,
        'comments': comments,
        'rejection_email_template': rejection_email_template,
        'pipeline_stages': pipeline_stages,
        'next_sub_statuses': next_sub_statuses,
        'current_stage': current_stage,
        'current_sub_status': current_sub_status,
        'current_stage_index': current_stage_index
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'core/partials/candidate_process_content.html', context)
    return render(request, 'core/candidate_recruiting_process.html', context)

@login_required
def search_candidates(request):
    """Simple candidate search by name."""
    try:
        query = request.GET.get('q', '').strip()
        
        # Get all candidates if no query, otherwise filter by name
        candidates = Candidate.objects.all()
        if query:
            candidates = candidates.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )
        
        # Limit to first 50 candidates
        candidates = candidates[:50]
        
        # Format results
        results = []
        for candidate in candidates:
            results.append({
                'id': candidate.id,
                'name': f"{candidate.first_name} {candidate.last_name}",
                'email': candidate.email or '',
                'phone': candidate.phone or '',
            })
        
        return JsonResponse({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def add_candidate_to_position(request, position_id):
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method'
        }, status=405)

    try:
        position = get_object_or_404(Position, id=position_id)
        candidate_id = request.POST.get('candidate')
        
        if not candidate_id:
            return JsonResponse({
                'success': False,
                'error': 'Candidate ID is required'
            }, status=400)

        candidate = get_object_or_404(Candidate, id=candidate_id)
        
        # Check if a recruiting process already exists
        if RecruitingProcess.objects.filter(candidate=candidate, position=position).exists():
            return JsonResponse({
                'success': False,
                'error': 'This candidate is already in the recruiting process for this position'
            }, status=400)

        # Get the first stage and sub-status for the client
        first_stage = position.client.pipeline_stages.order_by('order').first()
        if not first_stage:
            return JsonResponse({
                'success': False,
                'error': 'No pipeline stages configured for this client'
            }, status=400)
            
        first_sub_status = first_stage.sub_statuses.order_by('order').first()
        if not first_sub_status:
            return JsonResponse({
                'success': False,
                'error': 'No sub-statuses configured for the first pipeline stage'
            }, status=400)

        # Create the recruiting process with the first stage and sub-status
        process = RecruitingProcess.objects.create(
            candidate=candidate,
            position=position,
            stage=first_stage,
            sub_status=first_sub_status
        )

        return JsonResponse({
            'success': True,
            'message': 'Candidate added successfully'
        })

    except Position.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Position not found'
        }, status=404)
    except Candidate.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Candidate not found'
        }, status=404)
    except Exception as e:
        print(f"Error adding candidate: {str(e)}")  # Add logging
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

def delete_recruiting_process(request, position_id, process_id):
    process = get_object_or_404(RecruitingProcess, id=process_id)
    process.delete()
    
    if request.headers.get('HX-Request'):
        return redirect('position_recruiting_process', position_id=position_id)
    return redirect('position_recruiting_process', position_id=position_id)

def search_competencies(request):
    query = request.GET.get('q', '')
    competencies = Competency.objects.filter(name__icontains=query)[:10]
    results = [{'id': str(comp.id), 'text': comp.name} for comp in competencies]
    
    # If query doesn't match any existing competencies, add option to create new
    if query and not any(r['text'].lower() == query.lower() for r in results):
        results.append({'id': f"new:{query}", 'text': f'Add "{query}" as new competency'})
    
    return JsonResponse({'results': results})

def search_languages(request):
    query = request.GET.get('q', '')
    languages = Language.objects.filter(name__icontains=query)[:10]
    results = [{'id': str(lang.id), 'text': lang.name} for lang in languages]
    
    # If query doesn't match any existing languages, add option to create new
    if query and not any(r['text'].lower() == query.lower() for r in results):
        results.append({'id': f"new:{query}", 'text': f'Add "{query}" as new language'})
    
    return JsonResponse({'results': results})

def schedule_rejection_email(request, process_id):
    if request.method == 'POST':
        process = get_object_or_404(RecruitingProcess, id=process_id)
        try:
            # Get email content from request
            data = json.loads(request.body)
            email_subject = data.get('subject', f"Application Status for {process.position.title}")
            email_body = data.get('body', get_rejection_email_template(process))
            
            # Create rejection email
            rejection_email = RejectionEmail.objects.create(
                recruiting_process=process,
                scheduled_date=timezone.now(),
                email_subject=email_subject,
                email_body=email_body,
                status='pending'
            )
            
            # Send the email immediately
            if rejection_email.send_email():
                return JsonResponse({
                    'status': 'success',
                    'sent_at': rejection_email.sent_at.isoformat() if rejection_email.sent_at else None
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Failed to send email'
                })
                
        except Exception as e:
            print(f"Error scheduling rejection email: {str(e)}")  # For debugging
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def get_rejection_email_template(process):
    template = f"""Dear {process.candidate.first_name},

Thank you for your interest in the {process.position.title} position at {process.position.client.name} and for taking the time to participate in our recruitment process.

After careful consideration of your profile and qualifications, we regret to inform you that we have decided to move forward with other candidates whose experience more closely matches our current requirements.

We appreciate your interest in joining our team and would like to keep your profile in our database for future opportunities that might better match your skills and experience.

We wish you the best in your career endeavors.

Best regards,
{process.position.client.name} Recruitment Team"""
    
    return template

def update_recruiting_process_status(request, process_id):
    if request.method == 'POST':
        process = get_object_or_404(RecruitingProcess, id=process_id)
        new_status = request.POST.get('status')
        
        if new_status in dict(RecruitingProcess.STATUS_CHOICES):
            process.status = new_status
            process.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Status updated successfully'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid status value'
            })
            
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

def recruitment_statistics(request):
    from django.db.models import Count
    from .models import RecruitingProcess, Recruiter
    from django.utils import timezone
    from datetime import datetime, timedelta

    # Get the current month and last month
    today = timezone.now()
    current_month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    next_month_start = (current_month_start + timedelta(days=32)).replace(day=1)

    # Get recruiters
    calin = Recruiter.objects.filter(first_name='Calin').first()
    emil = Recruiter.objects.filter(first_name='Emil').first()

    # Current month statistics
    team_current_month = RecruitingProcess.objects.filter(
        created_at__gte=current_month_start,
        created_at__lt=next_month_start
    ).count()

    calin_current_month = RecruitingProcess.objects.filter(
        created_at__gte=current_month_start,
        created_at__lt=next_month_start,
        candidate__consultant=calin
    ).count() if calin else 0

    emil_current_month = RecruitingProcess.objects.filter(
        created_at__gte=current_month_start,
        created_at__lt=next_month_start,
        candidate__consultant=emil
    ).count() if emil else 0

    # Last month statistics
    team_last_month = RecruitingProcess.objects.filter(
        created_at__gte=last_month_start,
        created_at__lt=current_month_start
    ).count()

    calin_last_month = RecruitingProcess.objects.filter(
        created_at__gte=last_month_start,
        created_at__lt=current_month_start,
        candidate__consultant=calin
    ).count() if calin else 0

    emil_last_month = RecruitingProcess.objects.filter(
        created_at__gte=last_month_start,
        created_at__lt=current_month_start,
        candidate__consultant=emil
    ).count() if emil else 0

    # Closed positions
    team_closed_positions = RecruitingProcess.objects.filter(
        status='accepted',
        created_at__gte=current_month_start,
        created_at__lt=next_month_start
    ).count()

    calin_closed_positions = RecruitingProcess.objects.filter(
        status='accepted',
        created_at__gte=current_month_start,
        created_at__lt=next_month_start,
        candidate__consultant=calin
    ).count() if calin else 0

    emil_closed_positions = RecruitingProcess.objects.filter(
        status='accepted',
        created_at__gte=current_month_start,
        created_at__lt=next_month_start,
        candidate__consultant=emil
    ).count() if emil else 0

    context = {
        'team_current_month': team_current_month,
        'calin_current_month': calin_current_month,
        'emil_current_month': emil_current_month,
        'team_last_month': team_last_month,
        'calin_last_month': calin_last_month,
        'emil_last_month': emil_last_month,
        'team_closed_positions': team_closed_positions,
        'calin_closed_positions': calin_closed_positions,
        'emil_closed_positions': emil_closed_positions,
    }
    
    return render(request, 'core/recruitment_statistics.html', context)

def recruitment_statistics_details(request):
    from django.db.models import Count
    from .models import RecruitingProcess

    # Get counts for different stages across all recruiters
    stats = {
        'new_processes': RecruitingProcess.objects.filter(status='new').count(),
        'phone_interview': RecruitingProcess.objects.filter(status='phone_interview').count(),
        'client_interview': RecruitingProcess.objects.filter(status='client_interview').count(),
        'validation': RecruitingProcess.objects.filter(status='validation').count(),
        'waiting_feedback': RecruitingProcess.objects.filter(status='waiting_feedback').count(),
        'hired': RecruitingProcess.objects.filter(status='accepted').count(),
    }

    context = {
        'stats': stats,
    }
    
    return render(request, 'core/recruitment_statistics_details.html', context)

def dashboard(request):
    from django.utils import timezone
    from datetime import timedelta
    import json

    # Calculate time ranges
    now = timezone.now()
    month_ago = now - timedelta(days=30)
    week_ago = now - timedelta(days=7)

    # Time to hire metrics
    completed_processes = RecruitingProcess.objects.filter(
        stage__key='offered',  # Changed from status='accepted'
        created_at__gte=month_ago
    )
    
    # Calculate average time to hire
    total_days = 0
    process_count = 0
    for process in completed_processes:
        days = (now - process.created_at).days
        total_days += days
        process_count += 1
    
    avg_time_to_hire = round(total_days / process_count) if process_count > 0 else 0
    
    # Last month calculations
    last_month_processes = RecruitingProcess.objects.filter(
        stage__key='offered',  # Changed from status='accepted'
        created_at__gte=month_ago - timedelta(days=30),
        created_at__lt=month_ago
    )
    
    # Calculate last month's average
    last_month_total = 0
    last_month_count = 0
    for process in last_month_processes:
        days = (now - process.created_at).days
        last_month_total += days
        last_month_count += 1
    
    last_month_avg = last_month_total / last_month_count if last_month_count > 0 else 0
    
    # Calculate trend
    if last_month_avg > 0:
        time_to_hire_trend = round(((avg_time_to_hire - last_month_avg) / last_month_avg) * 100) if process_count > 0 else 0
    else:
        time_to_hire_trend = 0

    # Open positions and filled positions
    open_positions_count = Position.objects.filter(status='open').count()
    positions_filled_count = Position.objects.filter(
        recruitingprocess__stage__key='offered',  # Changed from status='closed'
        recruitingprocess__created_at__gte=month_ago
    ).distinct().count()

    # Active candidates
    active_candidates_count = RecruitingProcess.objects.exclude(
        stage__key__in=['offered', 'rejected']  # Changed from status__in
    ).count()
    
    new_candidates_count = RecruitingProcess.objects.filter(
        created_at__gte=week_ago
    ).count()

    # Interview success rate
    total_interviews = RecruitingProcess.objects.filter(
        stage__key__in=['screening', 'client_interview'],  # Changed from status__in
        created_at__gte=month_ago
    ).count()
    
    successful_interviews = RecruitingProcess.objects.filter(
        stage__key='offered',  # Changed from status='accepted'
        created_at__gte=month_ago
    ).count()
    
    success_rate = round((successful_interviews / total_interviews * 100) if total_interviews > 0 else 0)

    # Interviews this week
    interviews_this_week = RecruitingProcess.objects.filter(
        stage__key__in=['screening', 'client_interview'],  # Changed from status__in
        created_at__gte=week_ago
    ).count()

    # Pipeline stages
    stages = [
        {'name': 'New', 'key': 'pending_screening'},
        {'name': 'Screening', 'key': 'screening'},
        {'name': 'Validation', 'key': 'validation'},
        {'name': 'Client Interview', 'key': 'client_interview'},
        {'name': 'Offered', 'key': 'offered'},
    ]

    total_active = RecruitingProcess.objects.exclude(
        stage__key__in=['offered', 'rejected']  # Changed from status__in
    ).count()

    pipeline_stages = []
    for stage in stages:
        count = RecruitingProcess.objects.filter(stage__key=stage['key']).count()
        percentage = (count / total_active * 100) if total_active > 0 else 0
        avg_time = RecruitingProcess.objects.filter(
            stage__key=stage['key']  # Changed from status
        ).aggregate(
            avg_days=Avg(models.F('created_at') - models.F('created_at'))
        )['avg_days']
        
        pipeline_stages.append({
            'name': stage['name'],
            'count': count,
            'percentage': round(percentage),
            'avg_time': round(avg_time.days if avg_time else 0)
        })

    # Recent activities
    recent_activities = []
    recent_processes = RecruitingProcess.objects.select_related(
        'candidate', 'position', 'stage'  # Added stage
    ).order_by('-created_at')[:10]

    for process in recent_processes:
        activity_type = 'status_change'
        if process.stage.key in ['screening', 'client_interview']:  # Changed from status
            activity_type = 'interview'
        
        recent_activities.append({
            'type': activity_type,
            'description': f"{process.candidate.first_name} - {process.stage.name}",  # Changed from status
            'timestamp': process.created_at.strftime("%Y-%m-%d %H:%M")
        })

    context = {
        'avg_time_to_hire': avg_time_to_hire,
        'time_to_hire_trend': time_to_hire_trend,
        'open_positions_count': open_positions_count,
        'positions_filled_count': positions_filled_count,
        'active_candidates_count': active_candidates_count,
        'new_candidates_count': new_candidates_count,
        'success_rate': success_rate,
        'interviews_this_week': interviews_this_week,
        'pipeline_stages': pipeline_stages,
        'recent_activities': recent_activities,
    }

    return render(request, 'core/dashboard.html', context)

def parse_boolean_search(query):
    """Parse boolean search query and return Q objects"""
    # Replace AND, OR, NOT with & | ~
    query = re.sub(r'\bAND\b', '&', query, flags=re.IGNORECASE)
    query = re.sub(r'\bOR\b', '|', query, flags=re.IGNORECASE)
    query = re.sub(r'\bNOT\b', '~', query, flags=re.IGNORECASE)
    
    try:
        # Build Q objects based on the query
        terms = re.findall(r'\w+', query)
        q_objects = Q()
        
        for term in terms:
            if term not in ['&', '|', '~']:
                # Prioritize direct name matches
                name_query = (
                    Q(first_name__icontains=term) |
                    Q(last_name__icontains=term)
                )
                # Add other fields with lower priority
                other_query = (
                    Q(email__icontains=term) |
                    Q(competencies__name__icontains=term) |
                    Q(languages__name__icontains=term)
                )
                q_objects |= (name_query | other_query)
        
        return q_objects
    except:
        return None

def extract_resume_content(resume_file):
    """Extract text content from resume file"""
    try:
        file_extension = resume_file.name.split('.')[-1].lower()
        content = ''
        
        if file_extension == 'pdf':
            # Read PDF content
            pdf_reader = PyPDF2.PdfReader(resume_file)
            for page in pdf_reader.pages:
                content += page.extract_text()
                
        elif file_extension in ['doc', 'docx']:
            # Read Word document content
            doc = docx.Document(resume_file)
            content = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            
        return content
    except Exception as e:
        print(f"Error extracting resume content: {str(e)}")
        return None

def calculate_match_scores(candidates, required_skills, required_languages):
    """Calculate match scores based on skills and languages"""
    total_required = len(required_skills) + len(required_languages)
    
    for candidate in candidates:
        if total_required == 0:
            candidate.match_score = 100
            continue
            
        matches = 0
        if required_skills:
            matches += candidate.competencies.filter(id__in=required_skills).count()
        if required_languages:
            matches += candidate.languages.filter(id__in=required_languages).count()
            
        candidate.match_score = round((matches / total_required) * 100)
    
    return sorted(candidates, key=lambda x: x.match_score, reverse=True)

def preview_resume(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    highlight_text = request.GET.get('highlight', '')
    
    if not candidate.resume:
        return HttpResponse('No resume available')
        
    # Get the file path
    file_path = os.path.join(settings.MEDIA_ROOT, str(candidate.resume))
    
    try:
        # Open the PDF
        doc = fitz.open(file_path)
        
        # Create a temporary file for the highlighted version
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            # If there's text to highlight
            if highlight_text:
                for page in doc:
                    # Search for text instances
                    text_instances = page.search_for(highlight_text)
                    
                    # Add highlight for each instance
                    for inst in text_instances:
                        highlight = page.add_highlight_annot(inst)
                        highlight.update()
            
            # Save the modified document
            doc.save(tmp_file.name)
            doc.close()
            
            # Read the temporary file
            with open(tmp_file.name, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/pdf')
                response['Content-Disposition'] = 'inline;'
                # Allow iframe display
                response['X-Frame-Options'] = 'SAMEORIGIN'
                return response
            
    except Exception as e:
        return HttpResponse(f'Error processing PDF: {str(e)}')
    finally:
        # Clean up
        if 'tmp_file' in locals():
            os.unlink(tmp_file.name)

def parse_cv(request):
    if request.method != 'POST' or 'cv_file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'No file uploaded'})
    
    cv_file = request.FILES['cv_file']
    
    try:
        # Extract text from PDF
        text_content = extract_resume_content(cv_file)
        if not text_content:
            return JsonResponse({'success': False, 'error': 'Could not extract text from file'})
        
        # Get OpenAI API key
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
        
        if not api_key:
            print("Debug: API Key not found in environment or settings")
            print(f"Environment variables: {os.environ.keys()}")
            return JsonResponse({
                'success': False, 
                'error': 'OpenAI API key is not configured. Please check your .env file and ensure OPENAI_API_KEY is set correctly.'
            })
        
        # Initialize OpenAI client with explicit API key
        client = openai.OpenAI(api_key=api_key)
        print("Debug: OpenAI client initialized with API key")
        
        # Use OpenAI to parse the CV
        prompt = f"""Please analyze this CV and extract the following information in JSON format:
        - Full name
        - Email
        - Phone number
        - Skills (as a list)
        - Work experience (as a list of objects with company, position, and duration)
        - Education (as a list of objects with institution, degree, and year)
        - Languages (as a list)

        CV text:
        {text_content}
        
        Return only the JSON object without any additional text. If any field is not found, return an empty string or empty list as appropriate."""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a CV parser that extracts structured information from CVs and returns it in JSON format."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Get the response content and parse it as JSON
        response_content = response.choices[0].message.content.strip()
        print("OpenAI Response:", response_content)  # Debug print
        
        # Strip code block annotations if present
        response_content = response_content.replace('```json', '').replace('```', '').strip()
        print("Cleaned Response:", response_content)  # Debug print
        
        parsed_data = json.loads(response_content)
        print("Parsed Data:", parsed_data)  # Debug print
        
        # Handle name parsing safely
        full_name = parsed_data.get('Full name', '').strip()  # Note the capital F in 'Full name'
        print("Full Name:", full_name)  # Debug print
        
        name_parts = full_name.split() if full_name else ['Unknown', 'Candidate']
        print("Name Parts:", name_parts)  # Debug print
        
        # Create new candidate with parsed data
        candidate = Candidate.objects.create(
            first_name=name_parts[0] if len(name_parts) > 0 else 'Unknown',
            last_name=' '.join(name_parts[1:]) if len(name_parts) > 1 else 'Candidate',
            email=parsed_data.get('Email', ''),  # Note the capital E in 'Email'
            phone=parsed_data.get('Phone number', ''),  # Note the capital P and space in 'Phone number'
            resume=cv_file
        )
        
        # Add skills
        for skill_name in parsed_data.get('Skills', []):  # Note the capital S in 'Skills'
            if skill_name and skill_name.strip():  # Only add non-empty skills
                skill, _ = Competency.objects.get_or_create(name=skill_name.strip())
                candidate.competencies.add(skill)
        
        # Add languages
        for language_name in parsed_data.get('Languages', []):  # Note the capital L in 'Languages'
            if language_name and language_name.strip():  # Only add non-empty languages
                language, _ = Language.objects.get_or_create(name=language_name.strip())
                candidate.languages.add(language)
        
        return JsonResponse({
            'success': True,
            'redirect_url': reverse('candidate_edit', kwargs={'pk': candidate.id})
        })
        
    except openai.OpenAIError as e:
        print(f"OpenAI API Error: {str(e)}")
        if settings.DEBUG:
            return JsonResponse({'success': False, 'error': f'OpenAI API Error: {str(e)}'})
        else:
            return JsonResponse({'success': False, 'error': 'Service temporarily unavailable'})
        
    except Exception as e:
        print(f"Error in parse_cv: {str(e)}")
        if settings.DEBUG:
            return JsonResponse({'success': False, 'error': str(e)})
        else:
            return JsonResponse({'success': False, 'error': 'An error occurred while processing the CV'})

def candidate_delete(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    if request.method == 'POST':
        # Delete the candidate's resume file if it exists
        if candidate.resume:
            try:
                if os.path.exists(candidate.resume.path):
                    os.remove(candidate.resume.path)
            except Exception as e:
                print(f"Error deleting resume file: {str(e)}")
        
        candidate.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def advanced_search(request):
    from candidates.models import Candidate, Competency, Language
    
    # Get all skills and languages for the form
    all_skills = Competency.objects.all().order_by('name')
    all_languages = Language.objects.all().order_by('name')
    
    # Initialize queryset
    candidates = Candidate.objects.all()
    
    if request.GET:
        # Boolean keyword search
        keywords = request.GET.get('keywords', '').strip()
        if keywords:
            # Parse boolean expression
            query = parse_boolean_search(keywords)
            if query:
                candidates = candidates.filter(query)
        
        # Skills search
        skills = request.GET.getlist('skills')
        if skills:
            candidates = candidates.filter(competencies__id__in=skills)
        
        # Languages search
        languages = request.GET.getlist('languages')
        if languages:
            candidates = candidates.filter(languages__id__in=languages)
        
        # Experience level search
        experience = request.GET.get('experience')
        if experience:
            # Add your experience level filtering logic here
            pass
        
        # Resume content search
        resume_content = request.GET.get('resume_content')
        if resume_content:
            # Get candidates with matching resume content
            matching_candidates = set()
            for candidate in candidates:
                if candidate.resume:
                    content = extract_resume_content(candidate.resume)
                    if content and resume_content.lower() in content.lower():
                        matching_candidates.add(candidate.id)
            
            if matching_candidates:
                candidates = candidates.filter(id__in=matching_candidates)
        
        # Ensure queryset is distinct before converting to list
        candidates = candidates.distinct()
        
        # Calculate match scores if needed
        if skills or languages:
            candidates_list = list(candidates)
            candidates = calculate_match_scores(candidates_list, skills, languages)
        
    context = {
        'candidates': candidates,
        'all_skills': all_skills,
        'all_languages': all_languages,
        'selected_skills': [int(s) for s in skills] if request.GET.get('skills') else [],
        'selected_languages': [int(l) for l in languages] if request.GET.get('languages') else [],
    }
    
    return render(request, 'core/advanced_search.html', context)

@login_required
def stage_candidates_api(request, position_id, stage_key):
    position = get_object_or_404(Position, id=position_id)
    stage = get_object_or_404(PipelineStage, client=position.client, key=stage_key)
    
    # Get processes for this stage
    processes = RecruitingProcess.objects.filter(
        position=position,
        stage=stage
    ).select_related(
        'candidate', 'sub_status'
    )
    
    # Group by sub-status
    sub_statuses_data = []
    for sub_status in stage.sub_statuses.all().order_by('order'):
        sub_status_processes = processes.filter(sub_status=sub_status)
        candidates = []
        
        for process in sub_status_processes:
            candidates.append({
                'id': process.id,
                'candidate': {
                    'id': process.candidate.id,
                    'first_name': process.candidate.first_name,
                    'last_name': process.candidate.last_name,
                },
                'source': process.candidate.source if hasattr(process.candidate, 'source') else "LinkedIn",
                'days_in_stage': (timezone.now().date() - process.created_at.date()).days,
                'interview_score': float(process.interview_score) if process.interview_score else None,
                'cv_match': process.cv_match
            })
        
        sub_statuses_data.append({
            'key': sub_status.key,
            'name': sub_status.name,
            'processes': candidates
        })
    
    return JsonResponse({
        'success': True,
        'stage_name': stage.name,
        'sub_statuses': sub_statuses_data
    })

@login_required
def create_client_api(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        use_default_pipeline = data.get('use_default_pipeline', True)
        pipeline_config = data.get('pipeline_config')
        
        if not name or not email:
            return JsonResponse({
                'success': False,
                'error': 'Name and email are required'
            })
        
        # Create the client without pipeline first
        client = Client.objects.create(
            name=name,
            email=email,
            phone=phone
        )
        
        # If not using default pipeline, delete any automatically created stages
        if not use_default_pipeline:
            client.pipeline_stages.all().delete()
            
            # If custom pipeline config is provided, create those stages
            if pipeline_config:
                for stage_data in pipeline_config:
                    stage = PipelineStage.objects.create(
                        client=client,
                        key=stage_data['key'],
                        name=stage_data['name'],
                        order=stage_data.get('order', 0),
                        color=stage_data.get('color', '#6B7280')
                    )
                    
                    # Create sub-statuses for this stage
                    for sub_status_data in stage_data.get('sub_statuses', []):
                        PipelineSubStatus.objects.create(
                            stage=stage,
                            key=sub_status_data['key'],
                            name=sub_status_data['name'],
                            order=sub_status_data.get('order', 0)
                        )
        
        return JsonResponse({
            'success': True,
            'client_id': client.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def save_pipeline_config(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        pipeline_config = data.get('pipeline')
        
        if not pipeline_config:
            return JsonResponse({
                'success': False,
                'error': 'Pipeline configuration is required'
            })
        
        # Validate pipeline configuration
        for stage in pipeline_config:
            if not stage.get('name'):
                return JsonResponse({
                    'success': False,
                    'error': 'Stage name is required'
                })
            
            for sub_status in stage.get('sub_statuses', []):
                if not sub_status.get('name'):
                    return JsonResponse({
                        'success': False,
                        'error': 'Sub-status name is required'
                    })
        
        return JsonResponse({
            'success': True,
            'pipeline_config': pipeline_config
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def candidate_profile(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    context = {
        'candidate': candidate,
    }
    return render(request, 'core/candidate_profile.html', context)
