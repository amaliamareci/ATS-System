from django import forms
from .models import RecruitingProcess

class RecruitingProcessForm(forms.ModelForm):
    class Meta:
        model = RecruitingProcess
        fields = ['candidate', 'position', 'stage', 'sub_status', 'interview_score', 'cv_match']
        widgets = {
            'candidate': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500 bg-white shadow-sm'}),
            'position': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500 bg-white shadow-sm'}),
            'stage': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500 bg-white shadow-sm'}),
            'sub_status': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500 bg-white shadow-sm'}),
            'interview_score': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500'}),
            'cv_match': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500'})
        } 