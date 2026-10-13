from django.contrib import admin
from .models import Claim, HandoffOTP, HandoffAuditLog


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'claimant', 'status', 'created_at', 'reviewed_by', 'reviewed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('item__title', 'claimant__username', 'description', 'review_notes')


@admin.register(HandoffOTP)
class HandoffOTPAdmin(admin.ModelAdmin):
    list_display = ('claim', 'otp_code', 'is_used', 'expires_at', 'verified_at', 'verified_by')
    list_filter = ('is_used',)
    search_fields = ('otp_code', 'claim__item__title', 'claim__claimant__username')


@admin.register(HandoffAuditLog)
class HandoffAuditLogAdmin(admin.ModelAdmin):
    list_display = ('item', 'claim', 'returned_to', 'confirmed_by', 'handoff_date')
    search_fields = ('item__title', 'returned_to__username', 'confirmed_by__username', 'notes')
