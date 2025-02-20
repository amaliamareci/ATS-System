from django import forms
from candidates.models import Candidate, Competency, Language
from positions.models import Position
from clients.models import Client
from meetings.models import Meeting
from recruiters.models import Recruiter
from recruitment.models import RecruitingProcess, PipelineStage, PipelineSubStatus

class CandidateForm(forms.ModelForm):
    positions = forms.ModelChoiceField(
        queryset=Position.objects.filter(status='open'),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500 bg-white shadow-sm'
        }),
        required=False,
        help_text='Select an open position (optional)'
    )

    # Add new fields for creating new competencies and languages
    new_competency = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500',
            'placeholder': 'Add new competency'
        })
    )
    new_language = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500',
            'placeholder': 'Add new language'
        })
    )

    class Meta:
        model = Candidate
        fields = ['first_name', 'last_name', 'email', 'phone', 'resume', 
                 'positions', 'consultant', 'competencies', 'languages', 'status']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500'}),
            'resume': forms.FileInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500'}),
            'consultant': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500 bg-white shadow-sm'}),
            'status': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500 bg-white shadow-sm'}),
            'competencies': forms.SelectMultiple(attrs={
                'class': 'select2 w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500',
            }),
            'languages': forms.SelectMultiple(attrs={
                'class': 'select2 w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500',
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        
        # Create new competencies first
        competencies_data = self.data.getlist('competencies')
        final_competencies = []
        
        for comp_id in competencies_data:
            if comp_id.startswith('new:'):
                name = comp_id.replace('new:', '')
                comp_obj, _ = Competency.objects.get_or_create(name=name)
                final_competencies.append(comp_obj.pk)
            else:
                final_competencies.append(comp_id)
        
        # Update the cleaned data with the new competencies
        cleaned_data['competencies'] = Competency.objects.filter(pk__in=final_competencies)

        # Create new languages first
        languages_data = self.data.getlist('languages')
        final_languages = []
        
        for lang_id in languages_data:
            if lang_id.startswith('new:'):
                name = lang_id.replace('new:', '')
                lang_obj, _ = Language.objects.get_or_create(name=name)
                final_languages.append(lang_obj.pk)
            else:
                final_languages.append(lang_id)
        
        # Update the cleaned data with the new languages
        cleaned_data['languages'] = Language.objects.filter(pk__in=final_languages)

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # Set the many-to-many relationships
            if 'competencies' in self.cleaned_data:
                instance.competencies.set(self.cleaned_data['competencies'])
            if 'languages' in self.cleaned_data:
                instance.languages.set(self.cleaned_data['languages'])
        return instance

class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['title', 'client', 'description', 'requirements', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500'}),
            'client': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500 bg-white shadow-sm'}),
            'description': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500', 'rows': 4}),
            'requirements': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500', 'rows': 4}),
            'status': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500 bg-white shadow-sm'})
        }

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'email', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500'})
        }

class RecruiterForm(forms.ModelForm):
    class Meta:
        model = Recruiter
        fields = ['first_name', 'last_name', 'email', 'phone', 'role']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500'}),
            'role': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500 bg-white shadow-sm'})
        }

class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ['recruiting_process', 'recruiter', 'meeting_type', 'date_time', 'notes']
        widgets = {
            'recruiting_process': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500 bg-white shadow-sm'}),
            'recruiter': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500 bg-white shadow-sm'}),
            'date_time': forms.DateTimeInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500',
                'type': 'datetime-local'
            }),
            'meeting_type': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500 bg-white shadow-sm'}),
            'notes': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:outline-none focus:border-blue-500', 'rows': 4})
        }

class RecruitingProcessForm(forms.ModelForm):
    class Meta:
        model = RecruitingProcess
        fields = ['position', 'candidate']
        widgets = {
            'position': forms.Select(attrs={'class': 'form-select'}),
            'candidate': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['position'].queryset = Position.objects.filter(status='open')
        self.fields['candidate'].queryset = Candidate.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        position = cleaned_data.get('position')
        candidate = cleaned_data.get('candidate')

        # Remove the client validation since recruiters don't have clients
        # if position and candidate and position.client != candidate.consultant.client:
        #     raise forms.ValidationError("Selected candidate does not belong to the position's client")

        return cleaned_data 