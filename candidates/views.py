from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Candidate, Competency, Language
from .forms import CandidateForm
from django.core.exceptions import ValidationError
import json
from django.db import models

@login_required
def candidate_list(request):
    candidates = Candidate.objects.all().order_by('-created_at')
    return render(request, 'candidates/candidate_list.html', {'candidates': candidates})

@login_required
def candidate_create(request):
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'candidate_id': candidate.id})
            return redirect('candidate_profile', pk=candidate.id)
    else:
        form = CandidateForm()
    return render(request, 'candidates/candidate_form.html', {'form': form})

@login_required
def candidate_edit(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            form.save()
            return redirect('candidate_profile', pk=pk)
    else:
        form = CandidateForm(instance=candidate)
    return render(request, 'candidates/candidate_form.html', {'form': form, 'candidate': candidate})

@login_required
def candidate_profile(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    return render(request, 'candidates/candidate_profile.html', {'candidate': candidate})

@login_required
def candidate_delete(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    if request.method == 'POST':
        candidate.delete()
        return redirect('candidate_list')
    return render(request, 'candidates/candidate_confirm_delete.html', {'candidate': candidate})

@login_required
def search_candidates(request):
    query = request.GET.get('q', '')
    try:
        candidates = Candidate.objects.filter(
            models.Q(first_name__icontains=query) |
            models.Q(last_name__icontains=query) |
            models.Q(email__icontains=query)
        )[:10]
        
        results = [{
            'id': candidate.id,
            'name': f"{candidate.first_name} {candidate.last_name}",
            'email': candidate.email,
            'phone': candidate.phone,
            'competencies': [comp.name for comp in candidate.competencies.all()]
        } for candidate in candidates]
        
        return JsonResponse({'success': True, 'results': results})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def preview_resume(request, candidate_id):
    candidate = get_object_or_404(Candidate, pk=candidate_id)
    if not candidate.resume:
        return JsonResponse({'error': 'No resume found'}, status=404)
    
    try:
        # Add your resume preview logic here
        return JsonResponse({'success': True, 'content': 'Resume content'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def parse_cv(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    if 'resume' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded'}, status=400)
    
    resume_file = request.FILES['resume']
    
    try:
        # Add your CV parsing logic here
        parsed_data = {'name': 'John Doe', 'email': 'john@example.com'}  # Replace with actual parsing
        return JsonResponse({'success': True, 'data': parsed_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
