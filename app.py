import streamlit as st
import pandas as pd

st.set_page_config(page_title="Analisis Data Otomatis", 
                   layout="wide",
                   initial_sidebar_state="expanded")
col_1, col_2 = st.columns([1, 5])
col_1.image("https://images.glints.com/unsafe/320x0/glints-dashboard.oss-ap-southeast-1.aliyuncs.com/company-logo/a2ebfb8120a9f7376b56e474d4c01562.jpeg", width=100)
col_2.markdown("<h1 style='text-align: center;'>Dashboard Data Analitik</h1>", unsafe_allow_html=True)

st.title("📊 Automatic Sales Dashboard Analitik")

pages = {
    "Sales": [
        st.Page("Sales.py", title="Sales", url_path="sales_data", icon="💸"),
        st.Page("custom_template.py", title="custom themplate", url_path="sales_product_data", icon="📦"),
    ],
    "Finance": [
        st.Page("learn.py", title="Invoice", url_path="finance_invoice_data", icon="🧾"),
        st.Page("learn.py", title="Expenses", url_path="finance_expenses_data", icon="📊"),
    ],
    "Logistics": [
        st.Page("learn.py", title="Purchase", url_path="logistics_purchase_data", icon="🛒"),
        st.Page("learn.py", title="Vendor", url_path="logistics_vendor_data", icon="🤝"),
        st.Page("learn.py", title="Inventory On Hand", url_path="logistics_inventory_data", icon="📦"),
    ]
}
# Importing the navigation module from Streamlit

pg = st.navigation(pages)
pg.run()


