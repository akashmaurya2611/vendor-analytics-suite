# dashboard/utils.py
import pandas as pd
from sqlalchemy import create_engine, text
from django.conf import settings
from urllib.parse import quote_plus

def run_ingestion():
    """
    Load data from data/sales.csv and data/purchases.csv and push to MySQL.
    """
    print("Starting Data Ingestion...")

    db = settings.DATABASES['default']
    safe_pw = quote_plus(db['PASSWORD'])
    connection_string = f"mysql+pymysql://{db['USER']}:{safe_pw}@{db['HOST']}/{db['NAME']}"
    engine = create_engine(connection_string)

    try:
        sales = pd.read_csv('data/sales.csv')
        purchases = pd.read_csv('data/purchases.csv')

        # ensure date columns
        if 'sale_date' in sales.columns:
            sales['sale_date'] = pd.to_datetime(sales['sale_date'], errors='coerce').dt.date

        if 'purchase_date' in purchases.columns:
            purchases['purchase_date'] = pd.to_datetime(purchases['purchase_date'], errors='coerce').dt.date

        # drop invalid rows
        sales = sales.dropna(subset=['vendor_id', 'brand_id', 'sales_dollars'])
        purchases = purchases.dropna(subset=['vendor_id', 'brand_id', 'purchase_cost'])

        with engine.begin() as conn:
            # clear tables (for deterministic presentation)
            conn.execute(text("DELETE FROM raw_sales"))
            conn.execute(text("DELETE FROM raw_purchases"))

            # vendors
            vendors = sales[['vendor_id', 'vendor_name']].drop_duplicates()
            vendors.to_sql('vendors', con=conn, if_exists='append', index=False)

            # sales
            sales[['vendor_id','brand_id','sales_dollars','quantity','sale_date']].to_sql(
                'raw_sales', con=conn, if_exists='append', index=False
            )

            # purchases
            purchases[['vendor_id','brand_id','purchase_cost','quantity','purchase_date']].to_sql(
                'raw_purchases', con=conn, if_exists='append', index=False
            )

        print("Data Ingestion Completed Successfully.")
    except Exception as e:
        print("Error during ingestion:", e)