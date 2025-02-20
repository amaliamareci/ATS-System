from django import forms
from .models import Candidate, Competency, Language
from positions.models import Position

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