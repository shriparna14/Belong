from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Item, Category, CampusLocation
from .forms import ItemForm
from .utils import generate_qr_code_base64
from claims.models import Claim
from accounts.models import Notification


def index_view(request):
    items = Item.objects.select_related('category', 'location', 'reporter').all()

    # Query search
    query = request.GET.get('q', '').strip()
    if query:
        items = items.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(specific_spot__icontains=query) |
            Q(location__name__icontains=query)
        )

    # Type filter (lost / found / returned / all)
    item_type = request.GET.get('type', '')
    if item_type in ['lost', 'found']:
        items = items.filter(item_type=item_type)
    elif item_type == 'returned':
        items = items.filter(status='returned')
    else:
        # By default exclude returned items from active feed unless explicitly chosen
        status_filter = request.GET.get('status', '')
        if not status_filter:
            items = items.exclude(status='archived')

    # Category filter
    category_slug = request.GET.get('category', '')
    if category_slug:
        items = items.filter(category__slug=category_slug)

    # Location filter
    location_id = request.GET.get('location', '')
    if location_id:
        items = items.filter(location_id=location_id)

    # Date range filters (Member 2)
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    if date_from:
        items = items.filter(incident_date__gte=date_from)
    if date_to:
        items = items.filter(incident_date__lte=date_to)

    # Aging filter
    aging = request.GET.get('aging', '')
    if aging == '1':
        threshold_days = getattr(settings, 'ITEM_AGING_DAYS_THRESHOLD', 30)
        cutoff_date = timezone.now() - timedelta(days=threshold_days)
        items = items.filter(created_at__lte=cutoff_date, status__in=['active', 'claim_pending'])

    # Sorting
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'oldest':
        items = items.order_by('created_at')
    else:
        items = items.order_by('-created_at')

    # Pagination
    paginator = Paginator(items, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    pagination_params = request.GET.copy()
    pagination_params.pop('page', None)

    # Check if any filter is active
    has_filters = bool(query or item_type or category_slug or location_id or date_from or date_to or (aging == '1') or (sort_by != 'newest'))

    # Recently added items for the showcase
    recently_added = Item.objects.select_related('category', 'location').exclude(status='archived').order_by('-created_at')[:4]

    context = {
        'items': page_obj,
        'recently_added': recently_added,
        'has_filters': has_filters,
        'query': query,
        'current_type': item_type,
        'current_category': category_slug,
        'current_location': location_id,
        'current_date_from': date_from,
        'current_date_to': date_to,
        'current_sort': sort_by,
        'current_aging': aging,
        'pagination_query': pagination_params.urlencode(),
    }
    return render(request, 'items/index.html', context)



def item_detail_view(request, pk):
    item = get_object_or_404(Item.objects.select_related('category', 'location', 'reporter'), pk=pk)
    
    # Check if user already filed a claim on this item
    user_claim = None
    item_claims = []
    is_owner = request.user.is_authenticated and item.reporter == request.user
    is_desk = request.user.is_authenticated and (request.user.is_staff or getattr(getattr(request.user, 'profile', None), 'role', '') == 'desk_admin')

    if request.user.is_authenticated:
        user_claim = Claim.objects.filter(item=item, claimant=request.user).first()
        if is_owner or is_desk:
            item_claims = Claim.objects.filter(item=item).order_by('-created_at')

    # Generate QR code URL for mobile intake badge
    qr_url = request.build_absolute_uri(reverse('items:detail', args=[item.pk]))
    qr_code_data = generate_qr_code_base64(qr_url)

    # Matching suggestions between lost and found reports (Member 2)
    opposite_type = 'found' if item.item_type == 'lost' else 'lost'
    match_candidates = Item.objects.filter(
        item_type=opposite_type,
        status='active'
    ).exclude(pk=item.pk)

    # Score candidates: same category (+2), same location (+1), incident date within 7 days (+1)
    matching_items = []
    for cand in match_candidates.select_related('category', 'location'):
        score = 0
        if cand.category_id and cand.category_id == item.category_id:
            score += 2
        if cand.location_id and cand.location_id == item.location_id:
            score += 1
        if abs((cand.incident_date - item.incident_date).days) <= 7:
            score += 1

        if score > 0:
            matching_items.append((score, cand))

    matching_items.sort(key=lambda x: x[0], reverse=True)
    matches = [m[1] for m in matching_items[:4]]


    context = {
        'item': item,
        'user_claim': user_claim,
        'item_claims': item_claims,
        'is_owner': is_owner,
        'is_desk': is_desk,
        'matches': matches,
        'qr_code_data': qr_code_data,
    }
    return render(request, 'items/detail.html', context)


@login_required
def item_create_view(request):
    initial_type = request.GET.get('type', 'lost')
    if initial_type not in ['lost', 'found']:
        initial_type = 'lost'

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.reporter = request.user
            item.save()

            if item.item_type == 'found' and (item.category_id or item.location_id):
                match_query = Q()
                if item.category_id:
                    match_query |= Q(category_id=item.category_id)
                if item.location_id:
                    match_query |= Q(location_id=item.location_id)

                matching_lost_items = Item.objects.filter(
                    item_type='lost',
                    status__in=['active', 'claim_pending'],
                ).filter(match_query).exclude(
                    reporter=request.user
                ).select_related('reporter')

                notified_reporters = set()
                for lost_item in matching_lost_items:
                    if lost_item.reporter_id in notified_reporters:
                        continue
                    notified_reporters.add(lost_item.reporter_id)
                    Notification.objects.create(
                        recipient=lost_item.reporter,
                        title="A similar item was reported found",
                        message=(
                            f"'{item.title}' may match your lost-item report "
                            f"'{lost_item.title}'. Review the public report and "
                            "use the secure claim process if it is yours."
                        ),
                        notification_type='matching_found_report',
                        link=reverse('items:detail', args=[item.pk]),
                    )

            messages.success(request, f"Your {item.get_item_type_display().lower()} listing has been published successfully!")
            return redirect('items:detail', pk=item.pk)
    else:
        form = ItemForm(initial={'item_type': initial_type, 'incident_date': timezone.now().date()})

    return render(request, 'items/create.html', {'form': form, 'initial_type': initial_type})


@login_required
def item_edit_view(request, pk):
    item = get_object_or_404(Item, pk=pk)
    is_desk = request.user.is_staff or getattr(getattr(request.user, 'profile', None), 'role', '') == 'desk_admin'

    if item.reporter != request.user and not is_desk:
        messages.error(request, "You do not have permission to edit this item listing.")
        return redirect('items:detail', pk=item.pk)

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Item details updated successfully.")
            return redirect('items:detail', pk=item.pk)
    else:
        form = ItemForm(instance=item)

    return render(request, 'items/edit.html', {'form': form, 'item': item})


@login_required
def item_delete_view(request, pk):
    item = get_object_or_404(Item, pk=pk)
    is_desk = request.user.is_staff or getattr(getattr(request.user, 'profile', None), 'role', '') == 'desk_admin'

    if item.reporter != request.user and not is_desk:
        messages.error(request, "You cannot delete this item.")
        return redirect('items:detail', pk=item.pk)

    if request.method == 'POST':
        item.delete()
        messages.success(request, "Listing deleted successfully.")
        return redirect('items:index')

    return render(request, 'items/confirm_delete.html', {'item': item})


@login_required
def item_resolve_view(request, pk):
    item = get_object_or_404(Item, pk=pk)
    is_desk = request.user.is_staff or getattr(getattr(request.user, 'profile', None), 'role', '') == 'desk_admin'

    if item.reporter != request.user and not is_desk:
        messages.error(request, "You are not authorized to update this listing.")
        return redirect('items:detail', pk=item.pk)

    if request.method == 'POST':
        item.status = 'returned'
        item.save()
        messages.success(request, f"'{item.title}' has been marked as resolved and reunited with owner!")
    return redirect('items:detail', pk=item.pk)


@login_required
def item_dispose_view(request, pk):
    item = get_object_or_404(Item, pk=pk)
    is_desk = request.user.is_staff or getattr(getattr(request.user, 'profile', None), 'role', '') == 'desk_admin'

    if not is_desk:
        messages.error(request, "Only Campus Desk Officers or Administrators can record item disposal.")
        return redirect('items:detail', pk=item.pk)

    if request.method == 'POST':
        action_type = request.POST.get('disposal_action', 'Disposed / Recycled')
        notes = request.POST.get('disposal_notes', '').strip()
        item.status = 'archived'
        item.holding_location = f"Archived: {action_type} - {notes}" if notes else f"Archived: {action_type}"
        item.save()
        messages.success(request, f"Item #{item.pk} ({item.title}) has been safely archived/disposed: {action_type}.")
        return redirect('items:desk')

    return redirect('items:desk')


@login_required
def campus_desk_view(request):
    is_desk = request.user.is_staff or getattr(getattr(request.user, 'profile', None), 'role', '') == 'desk_admin'
    if not is_desk:
        messages.error(request, "Staff or Lost & Found Desk authorization required to access the campus desk.")
        return redirect('items:index')

    threshold_days = getattr(settings, 'ITEM_AGING_DAYS_THRESHOLD', 30)
    cutoff_date = timezone.now() - timedelta(days=threshold_days)
    
    aged_items = Item.objects.filter(
        created_at__lte=cutoff_date,
        status__in=['active', 'claim_pending']
    ).select_related('category', 'location', 'reporter').order_by('created_at')

    handoff_ready_items = Item.objects.filter(status='handoff_ready').select_related('category', 'location', 'reporter')
    recent_returned = Item.objects.filter(status='returned').order_by('-updated_at')[:10]
    archived_items = Item.objects.filter(status='archived').order_by('-updated_at')[:10]

    context = {
        'aged_items': aged_items,
        'handoff_ready_items': handoff_ready_items,
        'recent_returned': recent_returned,
        'archived_items': archived_items,
        'threshold_days': threshold_days,
    }
    return render(request, 'items/campus_desk.html', context)
