from django import forms
from .models import Meeting

class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ['recruiting_process', 'recruiter', 'meeting_type', 'date_time', 'notes']
        widgets = {
            'recruiting_process': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500 bg-white shadow-sm'}),
            'recruiter': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500 bg-white shadow-sm'}),
            'meeting_type': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500 bg-white shadow-sm'}),
            'date_time': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500',
                'type': 'datetime-local'
            }),
            'notes': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500', 'rows': 4})
        } 