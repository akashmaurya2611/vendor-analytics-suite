# dashboard/admin.py
from django.contrib import admin
from .models import VendorProfile

@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ('vendor_name', 'vendor_id', 'user', 'created_at')
    search_fields = ('vendor_name', 'user__username')