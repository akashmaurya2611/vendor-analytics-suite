# dashboard/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Router: admin → dashboard; vendor → portal
    path('', views.index, name='home'),

    # Admin vendor management
    path('admin-vendors/',          views.admin_vendors, name='admin_vendors'),
    path('admin-vendors/add/',      views.add_vendor,    name='add_vendor'),
    path('admin-vendors/delete/<int:profile_id>/', views.delete_vendor, name='delete_vendor'),

    # Vendor portal uploads
    path('portal/',         views.vendor_portal, name='vendor_portal'),
    path('portal/upload/',  views.vendor_upload, name='vendor_upload'),

    # Admin APIs
    path('api/data/',               views.api_data,              name='api_data'),
    path('api/summary/',            views.api_summary,           name='api_summary'),
    path('api/monthly/',            views.api_monthly_trend,     name='api_monthly_trend'),
    path('api/spend-distribution/', views.api_spend_distribution, name='api_spend_distribution'),
    path('api/vendors/',            views.api_vendors,           name='api_vendors'),
    path('api/upload/',             views.api_admin_upload,      name='api_admin_upload'),

    # Export
    path('export/',  views.export_excel, name='export_excel'),
]