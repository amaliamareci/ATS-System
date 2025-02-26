from django import forms
from .models import CandidateAssessment, QuestionResponse, CompetencyScore

class QuestionResponseForm(forms.ModelForm):
    class Meta:
        model = QuestionResponse
        fields = ['response_text', 'rating']
        widgets = {
            'response_text': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500',
                'rows': 3,
                'placeholder': 'Enter your response...'
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'hidden',  # We'll use custom star rating UI
                'min': 1,
                'max': 5
            })
        }

class CompetencyScoreForm(forms.ModelForm):
    class Meta:
        model = CompetencyScore
        fields = ['score']
        widgets = {
            'score': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500',
                'min': 1,
                'max': 10
            })
        }

class CandidateAssessmentForm(forms.ModelForm):
    class Meta:
        model = CandidateAssessment
        fields = ['overall_rating', 'job_match_percentage', 'key_strengths', 'final_recommendation']
        widgets = {
            'overall_rating': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500',
                'min': 0,
                'max': 10,
                'step': 0.1
            }),
            'job_match_percentage': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500',
                'min': 0,
                'max': 100
            }),
            'key_strengths': forms.SelectMultiple(attrs={
                'class': 'select2 w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500'
            }),
            'final_recommendation': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-primary-500 focus:border-primary-500',
                'rows': 4,
                'placeholder': 'Enter your final recommendation...'
            })
        } 