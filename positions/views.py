from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Position
from .forms import PositionForm
from candidates.models import Candidate
from recruitment.models import RecruitingProcess
from clients.models import Client
from django.db.models import Count, Q, Subquery, OuterRef

@login_required
def position_list(request):
    positions = Position.objects.all().order_by('-created_at')
    return render(request, 'positions/position_list.html', {'positions': positions})

@login_required
def position_create(request):
    if request.method == 'POST':
        form = PositionForm(request.POST)
        if form.is_valid():
            position = form.save()
            return redirect('position_overview', position_id=position.id)
    else:
        form = PositionForm()
    return render(request, 'positions/position_form.html', {'form': form})

@login_required
def add_position(request):
    if request.method == 'POST':
        form = PositionForm(request.POST)
        if form.is_valid():
            position = form.save()
            return redirect('position_overview', position_id=position.id)
    else:
        form = PositionForm()
    return render(request, 'positions/position_form.html', {'form': form})

@login_required
def active_positions(request):
    # Get all clients with their positions
    clients = Client.objects.prefetch_related(
        'positions',
        'positions__recruitingprocess_set',
        'positions__recruitingprocess_set__candidate',
        'positions__recruitingprocess_set__candidate__consultant'
    ).all()

    print("Debug: Starting position processing")  # Debug print

    # Calculate total open positions
    total_open_positions = Position.objects.filter(status='open').count()
    print(f"Debug: Found {total_open_positions} open positions")  # Debug print

    # Process each client's positions
    for client in clients:
        print(f"\nDebug: Processing client: {client.name}")  # Debug print
        
        # Filter active positions for this client
        client.active_positions = client.positions.filter(status='open').annotate(
            in_process_count=Count(
                'recruitingprocess',
                filter=~Q(recruitingprocess__stage__key__in=['offered', 'rejected'])
            ),
            hired_count=Count(
                'recruitingprocess',
                filter=Q(recruitingprocess__stage__key='offered')
            ),
            candidate_count=Count('recruitingprocess', distinct=True)
        )

        # Get consultants for each position
        for position in client.active_positions:
            print(f"\nDebug: Processing position: {position.title}")  # Debug print
            
            # Get recruiting processes for this position
            recruiting_processes = position.recruitingprocess_set.select_related(
                'candidate',
                'candidate__consultant'
            ).all()
            
            print(f"Debug: Found {recruiting_processes.count()} recruiting processes")  # Debug print
            
            # Get unique consultants from candidates
            consultants = []
            for rp in recruiting_processes:
                print(f"Debug: Processing recruiting process {rp.id}")  # Debug print
                if rp.candidate:
                    print(f"Debug: Found candidate: {rp.candidate.first_name} {rp.candidate.last_name}")  # Debug print
                    if rp.candidate.consultant:
                        consultant = rp.candidate.consultant
                        print(f"Debug: Found consultant: {consultant.first_name} {consultant.last_name}")  # Debug print
                        if consultant not in consultants:
                            consultants.append(consultant)
                            print(f"Debug: Added consultant to list")  # Debug print
            
            position.consultants = consultants
            position.consultant_count = len(consultants)
            print(f"Debug: Position has {len(consultants)} consultants")  # Debug print

    context = {
        'clients': clients,
        'total_open_positions': total_open_positions,
    }
    
    return render(request, 'core/active_positions.html', context)

@login_required
def position_overview(request, position_id):
    position = get_object_or_404(Position, pk=position_id)
    return render(request, 'positions/position_overview.html', {'position': position})

@login_required
def add_candidate_to_position(request, position_id):
    position = get_object_or_404(Position, pk=position_id)
    
    if request.method == 'POST':
        candidate_id = request.POST.get('candidate')
        if candidate_id:
            candidate = get_object_or_404(Candidate, pk=candidate_id)
            
            # Check if a recruiting process already exists
            if not RecruitingProcess.objects.filter(candidate=candidate, position=position).exists():
                RecruitingProcess.objects.create(
                    candidate=candidate,
                    position=position
                )
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Candidate already added to this position'})
        
        return JsonResponse({'success': False, 'error': 'No candidate specified'})
    
    return render(request, 'positions/add_candidate.html', {'position': position})
