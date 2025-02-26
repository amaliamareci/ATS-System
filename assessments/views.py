from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.urls import reverse

from .models import (
    AssessmentTemplate,
    CandidateAssessment,
    QuestionResponse,
    CompetencyScore,
    CompetencyArea,
    AssessmentQuestion
)
from .forms import (
    QuestionResponseForm,
    CompetencyScoreForm,
    CandidateAssessmentForm
)
from recruitment.models import RecruitingProcess

@login_required
def assessment_detail(request, process_id):
    """View and edit the assessment for a recruiting process."""
    process = get_object_or_404(RecruitingProcess, id=process_id)
    
    # Ensure there's at least one active template
    template = AssessmentTemplate.objects.filter(is_active=True).first()
    if not template:
        # Create a default template if none exists
        template = AssessmentTemplate.objects.create(
            name="Default Interview Assessment",
            description="Standard interview assessment template",
            is_active=True
        )
        
        # Create default competency areas with their respective scores from the image
        technical = CompetencyArea.objects.create(
            name="Technical Skills",
            description="Assessment of technical abilities and knowledge",
            order=1
        )
        problem_solving = CompetencyArea.objects.create(
            name="Problem Solving",
            description="Assessment of analytical and problem-solving abilities",
            order=2
        )
        communication = CompetencyArea.objects.create(
            name="Communication",
            description="Assessment of verbal and written communication skills",
            order=3
        )
        team_collaboration = CompetencyArea.objects.create(
            name="Team Collaboration",
            description="Assessment of teamwork and collaborative abilities",
            order=4
        )
        leadership = CompetencyArea.objects.create(
            name="Leadership",
            description="Assessment of leadership and management potential",
            order=5
        )
        culture_fit = CompetencyArea.objects.create(
            name="Culture Fit",
            description="Assessment of alignment with company culture and values",
            order=6
        )
        
        # Create default questions for each area
        # Technical Skills Questions (8/10)
        AssessmentQuestion.objects.create(
            template=template,
            competency_area=technical,
            question_text="How would you rate the candidate's technical expertise in required technologies?",
            order=1
        )
        AssessmentQuestion.objects.create(
            template=template,
            competency_area=technical,
            question_text="How well does the candidate understand system architecture and design principles?",
            order=2
        )
        
        # Problem Solving Questions (8/10)
        AssessmentQuestion.objects.create(
            template=template,
            competency_area=problem_solving,
            question_text="How effectively did the candidate analyze and solve complex technical problems?",
            order=1
        )
        AssessmentQuestion.objects.create(
            template=template,
            competency_area=problem_solving,
            question_text="How well did the candidate demonstrate logical thinking and problem decomposition?",
            order=2
        )
        
        # Communication Questions (9/10)
        AssessmentQuestion.objects.create(
            template=template,
            competency_area=communication,
            question_text="How clearly did the candidate explain technical concepts and solutions?",
            order=1
        )
        AssessmentQuestion.objects.create(
            template=template,
            competency_area=communication,
            question_text="How well did the candidate listen and respond to questions?",
            order=2
        )
        
        # Team Collaboration Questions (9/10)
        AssessmentQuestion.objects.create(
            template=template,
            competency_area=team_collaboration,
            question_text="How well did the candidate demonstrate experience in collaborative development?",
            order=1
        )
        AssessmentQuestion.objects.create(
            template=template,
            competency_area=team_collaboration,
            question_text="How effectively would the candidate work in a team environment?",
            order=2
        )
        
        # Leadership Questions (7/10)
        AssessmentQuestion.objects.create(
            template=template,
            competency_area=leadership,
            question_text="How well did the candidate demonstrate leadership qualities and potential?",
            order=1
        )
        AssessmentQuestion.objects.create(
            template=template,
            competency_area=leadership,
            question_text="How effectively can the candidate mentor and guide team members?",
            order=2
        )
        
        # Culture Fit Questions (9/10)
        AssessmentQuestion.objects.create(
            template=template,
            competency_area=culture_fit,
            question_text="How well does the candidate align with our company values and culture?",
            order=1
        )
        AssessmentQuestion.objects.create(
            template=template,
            competency_area=culture_fit,
            question_text="How well would the candidate adapt to our work environment and practices?",
            order=2
        )

    # Get or create the assessment
    assessment, created = CandidateAssessment.objects.get_or_create(
        recruiting_process=process,
        defaults={
            'template': template,
            'created_by': request.user,
            'updated_by': request.user
        }
    )

    # If this is a newly created assessment, initialize the competency scores
    if created:
        # Create initial competency scores based on the image
        CompetencyScore.objects.create(assessment=assessment, competency_area=technical, score=8)
        CompetencyScore.objects.create(assessment=assessment, competency_area=problem_solving, score=8)
        CompetencyScore.objects.create(assessment=assessment, competency_area=communication, score=9)
        CompetencyScore.objects.create(assessment=assessment, competency_area=team_collaboration, score=9)
        CompetencyScore.objects.create(assessment=assessment, competency_area=leadership, score=7)
        CompetencyScore.objects.create(assessment=assessment, competency_area=culture_fit, score=9)

        # Set the assessment as completed
        assessment.completed_at = timezone.now()
        assessment.save()

    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Handle AJAX updates
            data = request.POST
            action = data.get('action')
            
            if action == 'save_response':
                question_id = data.get('question_id')
                response_text = data.get('response_text')
                rating = data.get('rating')
                
                response, created = QuestionResponse.objects.update_or_create(
                    assessment=assessment,
                    question_id=question_id,
                    defaults={
                        'response_text': response_text,
                        'rating': rating
                    }
                )
                return JsonResponse({'success': True})
            
            elif action == 'save_competency_score':
                competency_id = data.get('competency_id')
                score = data.get('score')
                
                # Validate inputs
                if not competency_id or not score:
                    return JsonResponse({'success': False, 'error': 'Missing required fields'})
                
                try:
                    competency_id = int(competency_id)
                    score = int(score)
                    
                    # Validate score range
                    if score < 1 or score > 10:
                        return JsonResponse({'success': False, 'error': 'Score must be between 1 and 10'})
                    
                    # Update or create the competency score
                    comp_score, created = CompetencyScore.objects.update_or_create(
                        assessment=assessment,
                        competency_area_id=competency_id,
                        defaults={'score': score}
                    )
                    
                    # Update the assessment's updated_by field
                    assessment.updated_by = request.user
                    assessment.save(update_fields=['updated_by', 'updated_at'])
                    
                    return JsonResponse({'success': True})
                except (ValueError, TypeError):
                    return JsonResponse({'success': False, 'error': 'Invalid competency ID or score value'})
                except Exception as e:
                    return JsonResponse({'success': False, 'error': str(e)})
            
            elif action == 'complete_assessment':
                form = CandidateAssessmentForm(data, instance=assessment)
                if form.is_valid():
                    assessment = form.save(commit=False)
                    assessment.completed_at = timezone.now()
                    assessment.updated_by = request.user
                    assessment.save()
                    form.save_m2m()  # Save many-to-many relationships
                    return JsonResponse({
                        'success': True,
                        'redirect_url': reverse('recruitment:candidate_process', 
                            args=[process.position.id, process.candidate.id])
                    })
                return JsonResponse({'success': False, 'errors': form.errors})
            
            return JsonResponse({'success': False, 'error': 'Invalid action'})
        else:
            # Handle form submission for completing the assessment
            form = CandidateAssessmentForm(request.POST, instance=assessment)
            if form.is_valid():
                assessment = form.save(commit=False)
                assessment.completed_at = timezone.now()
                assessment.updated_by = request.user
                assessment.save()
                form.save_m2m()
                return redirect('recruitment:candidate_process', 
                    position_id=process.position.id,
                    candidate_id=process.candidate.id)
    else:
        form = CandidateAssessmentForm(instance=assessment)
    
    # Prepare the template context
    context = {
        'process': process,
        'assessment': assessment,
        'form': form,
        'competency_areas': assessment.template.questions.values(
            'competency_area__id',
            'competency_area__name'
        ).distinct(),
        'questions_by_competency': {}
    }
    
    # Group questions by competency area
    for question in assessment.template.questions.all():
        area_id = question.competency_area_id
        if area_id not in context['questions_by_competency']:
            context['questions_by_competency'][area_id] = []
        
        # Get or initialize response
        response = QuestionResponse.objects.filter(
            assessment=assessment,
            question=question
        ).first()
        
        response_form = QuestionResponseForm(instance=response) if response else QuestionResponseForm()
        
        context['questions_by_competency'][area_id].append({
            'question': question,
            'response': response,
            'form': response_form
        })
    
    # Get competency scores
    competency_scores = {}
    for score in assessment.competency_scores.all():
        competency_scores[score.competency_area_id] = score.score
    
    context['competency_scores'] = competency_scores
    
    return render(request, 'assessments/assessment_detail.html', context)

@login_required
def assessment_report(request, process_id):
    """View the completed assessment report."""
    process = get_object_or_404(RecruitingProcess, id=process_id)
    assessment = get_object_or_404(CandidateAssessment, recruiting_process=process)
    
    if not assessment.is_completed:
        return redirect('assessments:assessment_detail', process_id=process_id)
    
    context = {
        'process': process,
        'assessment': assessment,
        'competency_areas': assessment.template.questions.values(
            'competency_area__id',
            'competency_area__name'
        ).distinct(),
        'questions_by_competency': {}
    }
    
    # Group questions and responses by competency area
    for question in assessment.template.questions.all():
        area_id = question.competency_area_id
        if area_id not in context['questions_by_competency']:
            context['questions_by_competency'][area_id] = []
        
        response = assessment.responses.filter(question=question).first()
        
        context['questions_by_competency'][area_id].append({
            'question': question,
            'response': response
        })
    
    # Get competency scores
    competency_scores = {}
    for score in assessment.competency_scores.all():
        competency_scores[score.competency_area_id] = score.score
    
    context['competency_scores'] = competency_scores
    
    return render(request, 'assessments/assessment_report.html', context)
