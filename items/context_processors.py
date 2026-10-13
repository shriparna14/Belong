from .models import Item, Category, CampusLocation
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


def campus_stats(request):
    total_active = Item.objects.filter(status__in=['active', 'claim_pending', 'handoff_ready']).count()
    lost_count = Item.objects.filter(item_type='lost', status__in=['active', 'claim_pending']).count()
    found_count = Item.objects.filter(item_type='found', status__in=['active', 'claim_pending']).count()
    reunited_count = Item.objects.filter(status='returned').count()

    threshold_days = getattr(settings, 'ITEM_AGING_DAYS_THRESHOLD', 30)
    cutoff_date = timezone.now() - timedelta(days=threshold_days)
    aged_count = Item.objects.filter(status__in=['active', 'claim_pending'], created_at__lte=cutoff_date).count()

    categories = Category.objects.all()
    locations = CampusLocation.objects.all()

    unread_notifications_count = 0
    recent_notifications = []
    if request.user.is_authenticated:
        unread_notifications_count = request.user.notifications.filter(is_read=False).count()
        recent_notifications = request.user.notifications.all()[:5]

    return {
        'total_active_items': total_active,
        'lost_items_count': lost_count,
        'found_items_count': found_count,
        'reunited_count': reunited_count,
        'aged_items_count': aged_count,
        'global_categories': categories,
        'global_locations': locations,
        'aging_threshold_days': threshold_days,
        'unread_notifications_count': unread_notifications_count,
        'recent_notifications': recent_notifications,
    }
