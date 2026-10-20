from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Item, Category, CampusLocation
from .forms import ItemForm
from claims.models import Claim


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

    # Check if any filter is active
    has_filters = bool(query or item_type or category_slug or location_id or (aging == '1') or (sort_by != 'newest'))

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
        'current_sort': sort_by,
        'current_aging': aging,
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

    # Matching suggestions between lost and found reports (Member 2)
    opposite_type = 'found' if item.item_type == 'lost' else 'lost'
    matches = Item.objects.filter(
        item_type=opposite_type,
        status='active'
    ).filter(
        Q(category=item.category) | Q(location=item.location)
    ).exclude(pk=item.pk)[:4]

    context = {
        'item': item,
        'user_claim': user_claim,
        'item_claims': item_claims,
        'is_owner': is_owner,
        'is_desk': is_desk,
        'matches': matches,
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


def campus_desk_view(request):
    threshold_days = getattr(settings, 'ITEM_AGING_DAYS_THRESHOLD', 30)
    cutoff_date = timezone.now() - timedelta(days=threshold_days)
    
    aged_items = Item.objects.filter(
        created_at__lte=cutoff_date,
        status__in=['active', 'claim_pending']
    ).select_related('category', 'location', 'reporter').order_by('created_at')

    handoff_ready_items = Item.objects.filter(status='handoff_ready').select_related('category', 'location', 'reporter')
    recent_returned = Item.objects.filter(status='returned').order_by('-updated_at')[:10]

    context = {
        'aged_items': aged_items,
        'handoff_ready_items': handoff_ready_items,
        'recent_returned': recent_returned,
        'threshold_days': threshold_days,
    }
    return render(request, 'items/campus_desk.html', context)
