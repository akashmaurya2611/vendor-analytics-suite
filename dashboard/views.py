# dashboard/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum
from django.db import connection
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from django.conf import settings
from .models import VendorMetrics, RawSales, RawPurchases, VendorProfile
import pandas as pd
import io

# ---------------- helpers ----------------
def is_admin(user):
    return user.is_staff or user.is_superuser

def get_engine():
    db = settings.DATABASES['default']
    safe_pw = quote_plus(db['PASSWORD'])
    return create_engine(f"mysql+pymysql://{db['USER']}:{safe_pw}@{db['HOST']}/{db['NAME']}")

# ---------------- router ----------------
@login_required
def index(request):
    admin_flag = is_admin(request.user)
    if admin_flag:
        return render(request, 'dashboard/index.html', {
            'username': request.user.username,
            'is_admin': True,
            'vendor_name': 'Admin'
        })
    else:
        return redirect('vendor_portal')

# ---------------- admin vendor pages ----------------
@login_required
def admin_vendors(request):
    if not is_admin(request.user):
        return redirect('vendor_portal')

    profiles = VendorProfile.objects.select_related('user').all().order_by('vendor_name')
    return render(request, 'dashboard/admin_vendors.html', {
        'username': request.user.username,
        'profiles': profiles,
    })

@login_required
def add_vendor(request):
    if not is_admin(request.user):
        return redirect('vendor_portal')

    if request.method == 'POST':
        vendor_name = request.POST.get('vendor_name', '').strip()
        vendor_id   = request.POST.get('vendor_id', '').strip()
        username    = request.POST.get('username', '').strip()
        password    = request.POST.get('password', '').strip()

        errors = []
        if not vendor_name: errors.append("Vendor name is required.")
        if not vendor_id or not vendor_id.isdigit(): errors.append("Vendor ID must be a number.")
        if not username:    errors.append("Username is required.")
        if not password:    errors.append("Password is required.")
        if User.objects.filter(username=username).exists(): errors.append(f"Username '{username}' already taken.")
        if VendorProfile.objects.filter(vendor_id=vendor_id).exists(): errors.append(f"Vendor ID {vendor_id} already exists.")

        if errors:
            messages.error(request, " | ".join(errors))
        else:
            user = User.objects.create_user(username=username, password=password)
            VendorProfile.objects.create(
                user=user,
                vendor_id=int(vendor_id),
                vendor_name=vendor_name,
            )
            # Insert vendor into vendors table if missing
            try:
                engine = get_engine()
                with engine.begin() as conn:
                    conn.execute(text(
                        "INSERT IGNORE INTO vendors (vendor_id, vendor_name) VALUES (:vid, :vname)"
                    ), {"vid": int(vendor_id), "vname": vendor_name})
            except Exception as e:
                messages.warning(request, f"Vendor profile created but MySQL insert failed: {e}")

            messages.success(request, f"Vendor '{vendor_name}' created. Login: {username}")

        return redirect('admin_vendors')

    return redirect('admin_vendors')

@login_required
def delete_vendor(request, profile_id):
    if not is_admin(request.user):
        return redirect('vendor_portal')

    profile = get_object_or_404(VendorProfile, id=profile_id)
    name = profile.vendor_name
    profile.user.delete()
    messages.success(request, f"Vendor '{name}' deleted.")
    return redirect('admin_vendors')

# ---------------- vendor portal ----------------
@login_required
def vendor_portal(request):
    if is_admin(request.user):
        return redirect('home')

    try:
        profile = request.user.vendor_profile
    except VendorProfile.DoesNotExist:
        return HttpResponse("No vendor profile found for your account. Contact admin.", status=403)

    # vendor metrics if available
    try:
        metrics = VendorMetrics.objects.get(vendor_id=profile.vendor_id)
    except VendorMetrics.DoesNotExist:
        metrics = None

    return render(request, 'dashboard/vendor_portal.html', {
        'profile': profile,
        'metrics': metrics,
        'username': request.user.username,
    })


@login_required
def vendor_upload(request):
    if is_admin(request.user):
        return redirect('home')

    try:
        profile = request.user.vendor_profile
    except VendorProfile.DoesNotExist:
        return HttpResponse("No vendor profile.", status=403)

    if request.method != 'POST':
        return redirect('vendor_portal')

    sales_file = request.FILES.get('sales_file')
    purchases_file = request.FILES.get('purchases_file')

    if not sales_file and not purchases_file:
        messages.error(request, "No files selected.")
        return redirect('vendor_portal')

    engine = get_engine()
    
    # Process Sales File
    if sales_file:
        if not sales_file.name.endswith('.csv'):
            messages.error(request, "Sales file must be a CSV.")
        else:
            try:
                df_sales = pd.read_csv(sales_file)
                if df_sales.empty:
                    messages.warning(request, "Sales CSV is empty.")
                else:
                    df_sales['vendor_id'] = profile.vendor_id
                    required_sales = {'brand_id', 'sales_dollars', 'quantity', 'sale_date'}
                    missing_sales = required_sales - set(df_sales.columns)
                    
                    if missing_sales:
                        messages.error(request, f"Sales CSV missing columns: {', '.join(missing_sales)}")
                    else:
                        df_sales['sale_date'] = pd.to_datetime(df_sales['sale_date'], errors='coerce').dt.date
                        with engine.begin() as conn:
                            df_sales[['vendor_id','brand_id','sales_dollars','quantity','sale_date']].to_sql(
                                'raw_sales', con=conn, if_exists='append', index=False
                            )
                        messages.success(request, f"✓ {len(df_sales)} sales rows uploaded.")
            except Exception as e:
                messages.error(request, f"Sales CSV read failed: {e}")

    # Process Purchases File
    if purchases_file:
        if not purchases_file.name.endswith('.csv'):
            messages.error(request, "Purchases file must be a CSV.")
        else:
            try:
                df_purchases = pd.read_csv(purchases_file)
                if df_purchases.empty:
                    messages.warning(request, "Purchases CSV is empty.")
                else:
                    df_purchases['vendor_id'] = profile.vendor_id
                    required_purchases = {'brand_id', 'purchase_cost', 'quantity', 'purchase_date'}
                    missing_purchases = required_purchases - set(df_purchases.columns)
                    
                    if missing_purchases:
                        messages.error(request, f"Purchases CSV missing columns: {', '.join(missing_purchases)}")
                    else:
                        df_purchases['purchase_date'] = pd.to_datetime(df_purchases['purchase_date'], errors='coerce').dt.date
                        with engine.begin() as conn:
                            df_purchases[['vendor_id','brand_id','purchase_cost','quantity','purchase_date']].to_sql(
                                'raw_purchases', con=conn, if_exists='append', index=False
                            )
                        messages.success(request, f"✓ {len(df_purchases)} purchase rows uploaded.")
            except Exception as e:
                messages.error(request, f"Purchases CSV upload failed: {e}")

    return redirect('vendor_portal')


@login_required
def api_admin_upload(request):
    """API endpoint for admin dashboard to upload Sales/Purchases CSV."""
    if not is_admin(request.user):
        return JsonResponse({"success": False, "error": "Admin access required."}, status=403)

    if request.method != 'POST':
        return JsonResponse({"success": False, "error": "Only POST accepted."}, status=405)

    csv_file = request.FILES.get('file')
    upload_type = request.POST.get('type')  # 'sales' or 'purchases'

    if not csv_file:
        return JsonResponse({"success": False, "error": "No file uploaded."})

    try:
        df = pd.read_csv(csv_file)
        engine = get_engine()

        if upload_type == 'sales':
            required = {'vendor_id', 'brand_id', 'sales_dollars', 'quantity', 'sale_date'}
            missing = required - set(df.columns)
            if missing:
                return JsonResponse({"success": False, "error": f"Missing columns: {', '.join(missing)}"})

            df['sale_date'] = pd.to_datetime(df['sale_date'], errors='coerce').dt.date
            with engine.begin() as conn:
                # Note: Admin upload appends or replaces? Let's append for now as requested in implementation plan
                # Implementation plan says "Append new records. Existing data is preserved." (Wait, vendor_portal said replaces)
                # Dashboard template says: "Append new records. Existing data is preserved."
                df[['vendor_id','brand_id','sales_dollars','quantity','sale_date']].to_sql(
                    'raw_sales', con=conn, if_exists='append', index=False
                )
            return JsonResponse({"success": True, "message": f"Uploaded {len(df)} sales records."})

        elif upload_type == 'purchases':
            required = {'vendor_id', 'brand_id', 'purchase_cost', 'quantity', 'purchase_date'}
            missing = required - set(df.columns)
            if missing:
                return JsonResponse({"success": False, "error": f"Missing columns: {', '.join(missing)}"})

            df['purchase_date'] = pd.to_datetime(df['purchase_date'], errors='coerce').dt.date
            with engine.begin() as conn:
                df[['vendor_id','brand_id','purchase_cost','quantity','purchase_date']].to_sql(
                    'raw_purchases', con=conn, if_exists='append', index=False
                )
            return JsonResponse({"success": True, "message": f"Uploaded {len(df)} purchase records."})

        else:
            return JsonResponse({"success": False, "error": "Invalid upload type."})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


# ---------------- Admin APIs ----------------

@login_required
def api_summary(request):
    if not is_admin(request.user):
        return JsonResponse({"error": "Admin access required."}, status=403)
    data = VendorMetrics.objects.all()
    total_sales   = data.aggregate(Sum('total_sales'))['total_sales__sum']  or 0
    total_profit  = data.aggregate(Sum('gross_profit'))['gross_profit__sum'] or 0
    vendor_count  = data.count()
    profit_margin = round((float(total_profit) / float(total_sales) * 100), 2) if total_sales else 0

    return JsonResponse({
        "total_sales":   float(total_sales),
        "total_profit":  float(total_profit),
        "vendor_count":  vendor_count,
        "profit_margin": profit_margin,
    })


@login_required
def api_data(request):
    if not is_admin(request.user):
        return JsonResponse({"error": "Admin access required."}, status=403)
    filter_type = request.GET.get("type", "top")
    qs = VendorMetrics.objects.all().order_by(
        'total_sales' if filter_type == 'bottom' else '-total_sales'
    )[:10]
    return JsonResponse({
        "labels": [v.vendor_name  for v in qs],
        "sales":  [float(v.total_sales)   for v in qs],
        "profit": [float(v.gross_profit)  for v in qs],
        "margin": [float(v.profit_margin) for v in qs],
    })


@login_required
def api_monthly_trend(request):
    if not is_admin(request.user):
        return JsonResponse({"error": "Admin access required."}, status=403)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DATE_FORMAT(sale_date, '%Y-%m') AS month, SUM(sales_dollars)
            FROM raw_sales
            GROUP BY month ORDER BY month
        """)
        rows = cursor.fetchall()
    return JsonResponse({
        "months": [r[0] for r in rows],
        "sales":  [float(r[1]) for r in rows],
    })


@login_required
def api_spend_distribution(request):
    if not is_admin(request.user):
        return JsonResponse({"error": "Admin access required."}, status=403)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT brand_id, SUM(purchase_cost) AS total
            FROM raw_purchases GROUP BY brand_id ORDER BY total DESC LIMIT 8
        """)
        rows = cursor.fetchall()
    return JsonResponse({
        "labels": [f"Brand {r[0]}" for r in rows],
        "costs":  [float(r[1]) for r in rows],
    })


@login_required
def api_vendors(request):
    if not is_admin(request.user):
        return JsonResponse({"error": "Admin access required."}, status=403)
    sort  = request.GET.get('sort', 'total_sales')
    order = request.GET.get('order', 'desc')
    allowed = {'total_sales','gross_profit','profit_margin','vendor_name','vendor_id'}
    if sort not in allowed: sort = 'total_sales'
    qs = VendorMetrics.objects.all().order_by(f"{'-' if order=='desc' else ''}{sort}")
    return JsonResponse({"vendors": [
        {"id": v.vendor_id, "name": v.vendor_name,
         "sales": float(v.total_sales), "profit": float(v.gross_profit), "margin": float(v.profit_margin)}
        for v in qs
    ]})


@login_required
def export_excel(request):
    if not is_admin(request.user):
        return redirect('home')
    data = VendorMetrics.objects.all().values(
        'vendor_id', 'vendor_name', 'total_sales', 'gross_profit', 'profit_margin'
    )
    df = pd.DataFrame(list(data))
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=vendor_report.xlsx'
    df.to_excel(response, index=False)
    return response