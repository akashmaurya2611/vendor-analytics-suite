# dashboard/models.py
from django.db import models
from django.contrib.auth.models import User

# ─── Analytics View Model (read-only)
class VendorMetrics(models.Model):
    vendor_id     = models.IntegerField(primary_key=True)
    vendor_name   = models.CharField(max_length=255)
    total_sales   = models.DecimalField(max_digits=15, decimal_places=2)
    gross_profit  = models.DecimalField(max_digits=15, decimal_places=2)
    profit_margin = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed  = False
        db_table = 'v_vendor_metrics'

    def __str__(self):
        return self.vendor_name


# ─── Raw table models (read-only)
class RawSales(models.Model):
    vendor_id     = models.IntegerField()
    brand_id      = models.IntegerField()
    sales_dollars = models.DecimalField(max_digits=15, decimal_places=2)
    quantity      = models.IntegerField()
    sale_date     = models.DateField(null=True, blank=True)

    class Meta:
        managed  = False
        db_table = 'raw_sales'


class RawPurchases(models.Model):
    vendor_id     = models.IntegerField()
    brand_id      = models.IntegerField()
    purchase_cost = models.DecimalField(max_digits=15, decimal_places=2)
    quantity      = models.IntegerField()
    purchase_date = models.DateField(null=True, blank=True)

    class Meta:
        managed  = False
        db_table = 'raw_purchases'


# ─── Vendor Profile (Django-managed)
class VendorProfile(models.Model):
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')
    vendor_id   = models.IntegerField(unique=True)
    vendor_name = models.CharField(max_length=255)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vendor_profiles'

    def __str__(self):
        return f"{self.vendor_name} ({self.user.username})"