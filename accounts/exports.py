import csv
from django.http import HttpResponse
from items.models import Item
from claims.models import HandoffAuditLog

def export_items_csv_view(request):
    is_desk = request.user.is_staff or getattr(getattr(request.user, 'profile', None), 'role', '') == 'desk_admin'
    if not request.user.is_authenticated or not is_desk:
        return HttpResponse("Unauthorized", status=403)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="campus_lost_found_items.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Title', 'Type', 'Category', 'Campus Location', 'Specific Spot', 
        'Date Lost/Found', 'Status', 'Reporter', 'Created At'
    ])

    items = Item.objects.select_related('category', 'location', 'reporter').all().order_by('-created_at')
    for item in items:
        writer.writerow([
            item.id,
            item.title,
            item.get_item_type_display(),
            item.category.name if item.category else '',
            item.location.name if item.location else '',
            item.specific_spot or '',
            item.incident_date,
            item.get_status_display(),
            item.reporter.username if item.reporter else '',
            item.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])

    return response

def export_audit_logs_csv_view(request):
    is_desk = request.user.is_staff or getattr(getattr(request.user, 'profile', None), 'role', '') == 'desk_admin'
    if not request.user.is_authenticated or not is_desk:
        return HttpResponse("Unauthorized", status=403)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="campus_custody_audit_logs.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Log ID', 'Item Title', 'Claim ID', 'Returned To', 'Confirmed By', 'Notes', 'Handoff Date'
    ])

    logs = HandoffAuditLog.objects.select_related('item', 'claim', 'returned_to', 'confirmed_by').all().order_by('-handoff_date')
    for log in logs:
        writer.writerow([
            log.id,
            log.item.title if log.item else '',
            log.claim.id if log.claim else '',
            log.returned_to.username if log.returned_to else '',
            log.confirmed_by.username if log.confirmed_by else '',
            log.notes or '',
            log.handoff_date.strftime('%Y-%m-%d %H:%M:%S'),
        ])

    return response

