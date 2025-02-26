from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import RecruitingProcess, PipelineStage, PipelineSubStatus, StatusChange
from .forms import RecruitingProcessForm
from positions.models import Position
from candidates.models import Candidate
from meetings.models import Meeting
from assessments.models import CandidateAssessment
from core.views import get_rejection_email_template

@login_required
def recruiting_process_list(request):
    processes = RecruitingProcess.objects.all().order_by('-created_at')
    return render(request, 'recruitment/process_list.html', {'processes': processes})

@login_required
def recruiting_process_create(request):
    if request.method == 'POST':
        form = RecruitingProcessForm(request.POST)
        if form.is_valid():
            process = form.save()
            return redirect('recruitment:candidate_process', 
                          position_id=process.position.id,
                          candidate_id=process.candidate.id)
    else:
        form = RecruitingProcessForm()
    return render(request, 'recruitment/process_form.html', {'form': form})

@login_required
def recruiting_process_edit(request, pk):
    process = get_object_or_404(RecruitingProcess, pk=pk)
    if request.method == 'POST':
        form = RecruitingProcessForm(request.POST, instance=process)
        if form.is_valid():
            form.save()
            return redirect('recruitment:candidate_process', 
                          position_id=process.position.id,
                          candidate_id=process.candidate.id)
    else:
        form = RecruitingProcessForm(instance=process)
    return render(request, 'recruitment/process_form.html', {'form': form, 'process': process})

@login_required
def position_recruiting_process(request, position_id):
    position = get_object_or_404(Position, pk=position_id)
    processes = position.recruitingprocess_set.all()
    return render(request, 'recruitment/position_process.html', 
                 {'position': position, 'processes': processes})

@login_required
def candidate_recruiting_process(request, position_id, candidate_id):
    position = get_object_or_404(Position, id=position_id)
    candidate = get_object_or_404(Candidate, id=candidate_id)
    process = get_object_or_404(
        RecruitingProcess.objects.select_related('assessment'), 
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
            return redirect('recruitment:position_process', position_id=process.position.id)
        return redirect('recruitment:position_process', position_id=process.position.id)
    
    # Get all meetings for this process with recruiter data
    meetings = Meeting.objects.filter(recruiting_process=process).select_related('recruiter').order_by('-date_time')
    
    # Get comments for this process
    comments = process.comments.select_related('author').all()
    
    # Get the rejection email template to the context
    rejection_email_template = get_rejection_email_template(process)
    
    # Get all pipeline stages and sub-statuses for the client
    pipeline_stages = position.client.pipeline_stages.prefetch_related('sub_statuses').all()
    
    # Get or initialize assessment
    try:
        assessment = process.assessment
    except CandidateAssessment.DoesNotExist:
        assessment = None
    
    context = {
        'position': position,
        'candidate': candidate,
        'process': process,
        'meetings': meetings,
        'comments': comments,
        'rejection_email_template': rejection_email_template,
        'pipeline_stages': pipeline_stages,
        'assessment': assessment,
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'recruitment/partials/candidate_process_content.html', context)
    return render(request, 'recruitment/candidate_recruiting_process.html', context)

@login_required
def delete_recruiting_process(request, position_id, process_id):
    process = get_object_or_404(RecruitingProcess, pk=process_id)
    if request.method == 'POST':
        process.delete()
        return redirect('recruitment:position_process', position_id=position_id)
    return render(request, 'recruitment/process_confirm_delete.html', {'process': process})

@login_required
def update_recruiting_process_status(request, process_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    process = get_object_or_404(RecruitingProcess, pk=process_id)
    try:
        data = json.loads(request.body)
        stage_id = data.get('stage_id')
        sub_status_id = data.get('sub_status_id')
        
        if not stage_id or not sub_status_id:
            return JsonResponse({'error': 'Missing stage_id or sub_status_id'}, status=400)
        
        new_stage = get_object_or_404(PipelineStage, pk=stage_id)
        new_sub_status = get_object_or_404(PipelineSubStatus, pk=sub_status_id)
        
        # Create status change record
        StatusChange.objects.create(
            process=process,
            old_stage=process.stage,
            new_stage=new_stage,
            old_sub_status=process.sub_status,
            new_sub_status=new_sub_status
        )
        
        # Update process status
        process.stage = new_stage
        process.sub_status = new_sub_status
        process.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def stage_candidates_api(request, position_id, stage_key):
    position = get_object_or_404(Position, pk=position_id)
    processes = RecruitingProcess.objects.filter(
        position=position,
        stage__key=stage_key
    ).select_related('candidate')
    
    candidates = [{
        'id': process.candidate.id,
        'name': f"{process.candidate.first_name} {process.candidate.last_name}",
        'email': process.candidate.email,
        'status': process.sub_status.name,
        'process_id': process.id
    } for process in processes]
    
    return JsonResponse({'candidates': candidates})

@login_required
def save_pipeline_config(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        client_id = data.get('client_id')
        pipeline_config = data.get('pipeline_config')
        
        if not client_id or not pipeline_config:
            return JsonResponse({'error': 'Missing client_id or pipeline_config'}, status=400)
        
        # Clear existing pipeline stages
        PipelineStage.objects.filter(client_id=client_id).delete()
        
        # Create new pipeline stages
        for stage_data in pipeline_config:
            stage = PipelineStage.objects.create(
                client_id=client_id,
                key=stage_data['key'],
                name=stage_data['name'],
                order=stage_data['order'],
                color=stage_data.get('color', '#3B82F6')
            )
            
            # Create sub-statuses
            for sub_status in stage_data.get('sub_statuses', []):
                PipelineSubStatus.objects.create(
                    stage=stage,
                    key=sub_status['key'],
                    name=sub_status['name'],
                    order=sub_status.get('order', 0)
                )
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
