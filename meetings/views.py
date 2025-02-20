from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Meeting
from .forms import MeetingForm
from datetime import datetime, timedelta
from django.utils import timezone
from calendar import monthrange

@login_required
def meeting_list(request):
    meetings = Meeting.objects.all().order_by('-date_time')
    return render(request, 'meetings/meeting_list.html', {'meetings': meetings})

@login_required
def meeting_create(request):
    if request.method == 'POST':
        form = MeetingForm(request.POST)
        if form.is_valid():
            meeting = form.save()
            return redirect('meeting_list')
    else:
        form = MeetingForm()
    return render(request, 'meetings/meeting_form.html', {'form': form})

@login_required
def meeting_calendar(request):
    # Get selected recruiter from query params, default to 'all'
    selected_recruiter = request.GET.get('recruiter', 'all')
    
    # Get the current month and year
    today = timezone.now()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))
    
    # Get all days in the month
    _, num_days = monthrange(year, month)
    first_day = datetime(year, month, 1)
    last_day = datetime(year, month, num_days)
    
    # Filter meetings for the selected month
    meetings_query = Meeting.objects.filter(
        date_time__gte=first_day,
        date_time__lte=last_day
    )
    
    # Filter by recruiter if specified
    if selected_recruiter != 'all':
        meetings_query = meetings_query.filter(recruiter_id=selected_recruiter)
    
    # Organize meetings by day
    calendar_data = {}
    for day in range(1, num_days + 1):
        date = datetime(year, month, day)
        calendar_data[day] = meetings_query.filter(
            date_time__year=date.year,
            date_time__month=date.month,
            date_time__day=date.day
        )
    
    context = {
        'calendar_data': calendar_data,
        'year': year,
        'month': month,
        'selected_recruiter': selected_recruiter,
    }
    
    return render(request, 'meetings/calendar.html', context)
