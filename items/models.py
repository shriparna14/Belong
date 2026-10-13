from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True)
    icon = models.CharField(max_length=50, default='box', help_text="Icon identifier (e.g. laptop, key, wallet, id-card, book)")
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class CampusLocation(models.Model):
    name = models.CharField(max_length=100, unique=True)
    building_code = models.CharField(max_length=20, blank=True, help_text="e.g. LIB, ENG, STU")
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        if self.building_code:
            return f"{self.name} ({self.building_code})"
        return self.name


class Item(models.Model):
    ITEM_TYPE_CHOICES = [
        ('lost', 'Lost Item'),
        ('found', 'Found Item'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('claim_pending', 'Claim In Review'),
        ('handoff_ready', 'Approved / Ready for Pickup'),
        ('returned', 'Returned to Owner'),
        ('archived', 'Archived / Aged Out'),
    ]

    title = models.CharField(max_length=200)
    item_type = models.CharField(max_length=10, choices=ITEM_TYPE_CHOICES, default='lost')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='items')
    location = models.ForeignKey(CampusLocation, on_delete=models.SET_NULL, null=True, related_name='items')
    specific_spot = models.CharField(max_length=255, blank=True, help_text="e.g. Table 12, Floor 2, near silent study area")
    incident_date = models.DateField(help_text="Date lost or found")
    description = models.TextField(help_text="Detailed physical description visible to everyone")
    identifying_details = models.TextField(
        blank=True,
        help_text="Confidential: serial number, lock screen picture, unique scratch, or bag contents (only visible to reporter & desk officers for verification)"
    )
    image = models.ImageField(upload_to='items/%Y/%m/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_items')
    holding_location = models.CharField(
        max_length=150,
        default='Finder in possession',
        help_text="e.g. Finder in possession, Campus Central Security Desk Room 102, Library Front Desk"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_item_type_display().upper()}] {self.title} ({self.get_status_display()})"

    @property
    def days_open(self):
        delta = timezone.now() - self.created_at
        return max(0, delta.days)

    @property
    def is_aged(self):
        threshold = getattr(settings, 'ITEM_AGING_DAYS_THRESHOLD', 30)
        return self.days_open >= threshold and self.status in ['active', 'claim_pending']

    @property
    def is_claimable(self):
        return self.item_type == 'found' and self.status in ['active', 'claim_pending']

    @property
    def is_recent(self):
        delta = timezone.now() - self.created_at
        return delta.days <= 3
