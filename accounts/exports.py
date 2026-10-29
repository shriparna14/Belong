import csv
from django.http import HttpResponse
from items.models import Item
from claims.models import HandoffAuditLog

def export_items_csv_view(request):
    if not request.user.is_authenticated or not request.user.is_staff:
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
    if not request.user.is_authenticated or not request.user.is_staff:
        return HttpResponse("Unauthorized", status=403)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="campus_custody_audit_logs.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Log ID', 'Action', 'Item Title', 'Claimant', 'Verified By', 'Signature', 'Notes', 'Timestamp'
    ])

    logs = HandoffAuditLog.objects.select_related('claim__item', 'claim__claimant', 'verified_by').all().order_by('-timestamp')
    for log in logs:
        writer.writerow([
            log.id,
            log.get_action_display(),
            log.claim.item.title if log.claim and log.claim.item else '',
            log.claim.claimant.username if log.claim and log.claim.claimant else '',
            log.verified_by.username if log.verified_by else '',
            log.receiver_signature or '',
            log.notes or '',
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        ])

    return response
