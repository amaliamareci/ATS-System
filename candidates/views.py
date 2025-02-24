from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Candidate, Competency, Language, TechnicalNote
from .forms import CandidateForm
from django.core.exceptions import ValidationError
import json
from django.db import models

@login_required
def candidate_list(request):
    # Get filter parameters
    selected_source = request.GET.get('source')
    selected_skills = request.GET.getlist('skills')
    
    # Start with all candidates
    candidates = Candidate.objects.all()
    
    # Apply source filter
    if selected_source:
        candidates = candidates.filter(source=selected_source)
    
    # Apply skills filter
    if selected_skills:
        for skill in selected_skills:
            candidates = candidates.filter(competencies__name=skill)
    
    # Get all available skills and sources for filters
    all_skills = Competency.objects.all().order_by('name')
    all_sources = [choice[0] for choice in Candidate.source.field.choices]
    
    context = {
        'candidates': candidates.order_by('-created_at'),
        'all_skills': all_skills,
        'all_sources': all_sources,
        'selected_source': selected_source,
        'selected_skills': selected_skills,
    }
    
    return render(request, 'candidates/candidate_list.html', context)

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

@login_required
def add_technical_note(request, candidate_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    candidate = get_object_or_404(Candidate, pk=candidate_id)
    content = request.POST.get('content')
    
    if not content:
        return JsonResponse({'error': 'Note content is required'}, status=400)
    
    note = TechnicalNote.objects.create(
        candidate=candidate,
        author=request.user,
        content=content
    )
    
    return JsonResponse({
        'success': True,
        'note': {
            'id': note.id,
            'content': note.content,
            'author': f"{note.author.first_name} {note.author.last_name}",
            'created_at': note.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    })

@login_required
def delete_technical_note(request, candidate_id, note_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    note = get_object_or_404(TechnicalNote, pk=note_id, candidate_id=candidate_id)
    
    # Only allow the author to delete their own notes
    if note.author != request.user:
        return JsonResponse({'error': 'Not authorized to delete this note'}, status=403)
    
    note.delete()
    return JsonResponse({'success': True})
