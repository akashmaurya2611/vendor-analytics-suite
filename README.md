# Vendor Analytics Suite

## 📊 Overview
VendorAnalytics is a Django-based web application that empowers vendors to process, track, and analyze their sales and purchase data. It provides a secure vendor portal where users can seamlessly upload their CSV data and view a summarized dashboard with key performance indicators like Total Sales, Gross Profit, and Profit Margins.

## ✨ Features
* **Vendor Authentication:** Secure login and registration tailored to individual `VendorProfiles`.
* **Unified Data Upload:** Vendors can easily upload both `sales.csv` and `purchases.csv` data through a streamlined portal interface.
* **Automated Data Ingestion:** Fast and robust backend processing using `pandas` and `SQLAlchemy` to parse CSVs and populate the database.
* **Analytics Dashboard:** Real-time visibility into vendor performance metrics derived dynamically from underlying sales and purchase raw tables.
* **Role-Based Access:** Vendors only see their own metrics and uploaded data.

## 🛠 Tech Stack
* **Framework:** Django 6.0+
* **Data Processing:** Pandas, SQLAlchemy
* **Database:** MySQL / PostgreSQL (adaptable via `mysqlclient` & `psycopg2`)
* **Frontend:** Django Templates (HTML/CSS/JS)
* **Environment:** Python 3.x

## 📁 Project Structure
```text
VendorAnalytics/
├── dashboard/               # Main application app
│   ├── models.py            # Vendor, RawSales, RawPurchases, and View Models
│   ├── views.py             # Dashboard logic and upload handling routes
│   ├── utils.py             # Data ingestion and ETL functions (pandas/SQLAlchemy)
│   └── templates/           # HTML views including vendor_portal.html
├── vendor_project/          # Main Django project settings and routing
├── data/                    # Sample data directory (sales.csv, purchases.csv)
├── manage.py                # Django CLI utility
├── requirements.txt         # Project dependencies
└── .env                     # Environment variables (DB credentials, secret key)
```

## 🚀 Setup & Installation

**1. Clone the repository**
```bash
git clone <repository-url>
cd VendorAnalytics
```

**2. Create a virtual environment**
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up Environment Variables**
Ensure you have a [.env](cci:7://file:///c:/Users/akash/OneDrive/Desktop/VendorAnalytics/.env:0:0-0:0) file in the root directory (alongside `manage.py`) containing your configurations:
```env
SECRET_KEY=your-django-secret-key
DEBUG=True
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306
```

**5. Apply Database Migrations**
*Note: Some tables ([RawSales](cci:2://file:///c:/Users/akash/OneDrive/Desktop/VendorAnalytics/dashboard/models.py:21:0-30:30), [RawPurchases](cci:2://file:///c:/Users/akash/OneDrive/Desktop/VendorAnalytics/dashboard/models.py:33:0-42:34), `VendorMetrics`) are configured as `managed=False` in Django as they expect external/view configurations.*
```bash
python manage.py migrate
```

**6. Run the Development Server**
```bash
python manage.py runserver
```
The application will be accessible at `http://127.0.0.1:8000/`.

## 🤝 Usage
1. Open the app in your browser and register/login as a Vendor.
2. Navigate to the **Vendor Portal**.
3. Use the unified upload interface to submit your `sales.csv` and `purchases.csv` files.
4. Go to your Dashboard to view the updated sales metrics, gross profit, and margin summaries.
```
