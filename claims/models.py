from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random


class Claim(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('approved', 'Approved for Handoff'),
        ('rejected', 'Rejected'),
        ('completed', 'Handoff Completed'),
    ]

    item = models.ForeignKey('items.Item', on_delete=models.CASCADE, related_name='claims')
    claimant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='claims')
    description = models.TextField(help_text="Provide clear proof: secret marks, wallpaper, purchase details, or contents")
    proof_image = models.ImageField(upload_to='claims/%Y/%m/', blank=True, null=True, help_text="Optional photo of receipt, original box, or past photo with the item")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    review_notes = models.TextField(blank=True, help_text="Feedback or notes from the finder/campus desk")
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_claims')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Claim #{self.pk} on '{self.item.title}' by {self.claimant.username} ({self.get_status_display()})"


class HandoffOTP(models.Model):
    claim = models.OneToOneField(Claim, on_delete=models.CASCADE, related_name='handoff_otp')
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_handoffs')

    def __str__(self):
        return f"OTP for Claim #{self.claim.pk} (Code: {self.otp_code}, Used: {self.is_used})"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return (not self.is_used) and (not self.is_expired)

    @classmethod
    def generate_for_claim(cls, claim):
        # Generate 6 digit code
        code = f"{random.randint(100000, 999999)}"
        expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 15)
        expiry_time = timezone.now() + timedelta(minutes=expiry_minutes)

        otp, created = cls.objects.update_or_create(
            claim=claim,
            defaults={
                'otp_code': code,
                'expires_at': expiry_time,
                'is_used': False,
                'verified_at': None,
                'verified_by': None,
            }
        )
        return otp


class HandoffAuditLog(models.Model):
    item = models.ForeignKey('items.Item', on_delete=models.CASCADE, related_name='audit_logs')
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name='audit_logs')
    handoff_date = models.DateTimeField(auto_now_add=True)
    returned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_handoffs')
    confirmed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='logged_handoffs')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-handoff_date']

    def __str__(self):
        return f"Audit: '{self.item.title}' returned to {self.returned_to.username} on {self.handoff_date.strftime('%Y-%m-%d %H:%M')}"
