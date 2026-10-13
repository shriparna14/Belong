from django.contrib import admin
from .models import Category, CampusLocation, Item


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(CampusLocation)
class CampusLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'building_code')
    search_fields = ('name', 'building_code')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'item_type', 'category', 'location', 'status', 'reporter', 'incident_date', 'created_at', 'is_aged_badge')
    list_filter = ('item_type', 'status', 'category', 'location')
    search_fields = ('title', 'description', 'specific_spot', 'identifying_details')
    date_hierarchy = 'created_at'

    def is_aged_badge(self, obj):
        return obj.is_aged
    is_aged_badge.boolean = True
    is_aged_badge.short_description = 'Aging Alert'
