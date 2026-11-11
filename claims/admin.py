from django.contrib import admin
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from .models import Claim, HandoffOTP, HandoffAuditLog
from .emails import send_otp_email
from accounts.models import Notification


@admin.action(description='Approve selected pending claims and issue OTP')
def approve_claims(modeladmin, request, queryset):
    pending_claims = queryset.filter(status='pending').select_related(
        'item', 'claimant'
    )
    approved_count = 0

    for claim in pending_claims:
        claim.status = 'approved'
        claim.reviewed_by = request.user
        claim.reviewed_at = timezone.now()
        claim.review_notes = 'Approved from Django admin.'
        claim.save(update_fields=[
            'status', 'reviewed_by', 'reviewed_at', 'review_notes'
        ])

        claim.item.status = 'handoff_ready'
        claim.item.save(update_fields=['status', 'updated_at'])

        otp = HandoffOTP.generate_for_claim(claim)
        send_otp_email(claim, otp.otp_code)
        Notification.objects.create(
            recipient=claim.claimant,
            title='Claim Approved - OTP Ready!',
            message=(
                f"Your claim for '{claim.item.title}' was approved! "
                'Present your 6-digit OTP code during pickup.'
            ),
            notification_type='claim_approved',
            link=reverse('claims:detail', args=[claim.pk]),
        )
        approved_count += 1

    skipped_count = queryset.count() - approved_count
    if approved_count:
        modeladmin.message_user(
            request,
            f'{approved_count} claim(s) approved and OTP(s) issued.',
            messages.SUCCESS,
        )
    if skipped_count:
        modeladmin.message_user(
            request,
            f'{skipped_count} claim(s) skipped because they were not pending.',
            messages.WARNING,
        )


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'claimant', 'status', 'created_at', 'reviewed_by', 'reviewed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('item__title', 'claimant__username', 'description', 'review_notes')
    actions = (approve_claims,)


@admin.register(HandoffOTP)
class HandoffOTPAdmin(admin.ModelAdmin):
    list_display = ('claim', 'otp_code', 'is_used', 'expires_at', 'verified_at', 'verified_by')
    list_filter = ('is_used',)
    search_fields = ('otp_code', 'claim__item__title', 'claim__claimant__username')


@admin.register(HandoffAuditLog)
class HandoffAuditLogAdmin(admin.ModelAdmin):
    list_display = ('item', 'claim', 'returned_to', 'confirmed_by', 'handoff_date')
    search_fields = ('item__title', 'returned_to__username', 'confirmed_by__username', 'notes')
