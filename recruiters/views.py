from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Recruiter
from .forms import RecruiterForm

# Create your views here.

@login_required
def recruiter_list(request):
    recruiters = Recruiter.objects.all().order_by('user__first_name', 'user__last_name')
    return render(request, 'recruiters/recruiter_list.html', {'recruiters': recruiters})

@login_required
def recruiter_create(request):
    if request.method == 'POST':
        form = RecruiterForm(request.POST)
        if form.is_valid():
            recruiter = form.save()
            return redirect('recruiter_list')
    else:
        form = RecruiterForm()
    return render(request, 'recruiters/recruiter_form.html', {'form': form})
