import streamlit as st
import pandas as pd
from datetime import datetime
import os
import calendar
import re

st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="wide"
)

# ======================
# Helper Functions
# ======================
def clean_amount(series):
    if series is None or len(series) == 0:
        return series
    s = series.astype(str)
    s = s.str.replace(r"[$,€£¥\s]", "", regex=True)
    s = s.str.replace(r"[^0-9.\-]", "", regex=True)
    return pd.to_numeric(s, errors="coerce").fillna(0.0)

def normalize_date_column(series):
    if series is None or len(series) == 0:
        return series
    dt = pd.to_datetime(series, errors="coerce", dayfirst=False)
    if dt.isna().mean() > 0.3:
        dt = pd.to_datetime(series, errors="coerce", dayfirst=True)
    return dt.dt.strftime("%Y-%m-%d").fillna("")

def is_valid_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))

def sanitize_email(email: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "_", email.lower().strip())

def read_csv_chinese_safe(filepath_or_buffer):
    encodings = ["utf-8-sig", "utf-8", "gbk", "gb18030", "big5", "cp936"]
    last_error = None
    for enc in encodings:
        try:
            if hasattr(filepath_or_buffer, "seek"):
                filepath_or_buffer.seek(0)
            return pd.read_csv(filepath_or_buffer, encoding=enc)
        except Exception as e:
            last_error = e
            continue
    raise ValueError(f"Could not read CSV. Last error: {last_error}")

def has_corrupted_chinese(df: pd.DataFrame, text_cols) -> bool:
    for col in text_cols:
        if col in df.columns:
            s = df[col].astype(str)
            if s.str.contains(r"�|\?\?\?", regex=True, na=False).any():
                return True
    return False

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[\s\-]+", "_", regex=True)
        .str.replace(r"[^\w]", "", regex=True)
    )
    alias_map = {
        "date": "Date", "transaction_date": "Date", "txn_date": "Date",
        "payment_date": "Date", "posted_date": "Date",
        "category": "Category", "nature": "Category", "type": "Category",
        "expense_type": "Category", "account": "Category",
        "amount": "Amount", "value": "Amount", "price": "Amount",
        "cost": "Amount", "total": "Amount", "debit": "Amount",
        "currency": "Currency", "curr": "Currency", "ccy": "Currency",
        "currecny": "Currency",
        "vendor": "Vendor", "vendor_name": "Vendor", "payee": "Vendor",
        "merchant": "Vendor", "supplier": "Vendor", "store": "Vendor",
        "company": "Vendor", "business": "Vendor", "name": "Vendor", "party": "Vendor",
        "description": "Description", "desc": "Description", "memo": "Description",
        "details": "Description", "narrative": "Description",
        "remark": "Remark", "remarks": "Remark", "note": "Remark",
        "notes": "Remark", "comment": "Remark", "comments": "Remark",
        "source": "Source", "payment_method": "Source", "method": "Source",
        "user": "User", "email": "User",
        "customer": "Customer", "customer_name": "Customer", "client": "Customer",
    }
    rename = {col: alias_map.get(col, col.replace("_", " ").title()) for col in df.columns}
    df = df.rename(columns=rename)
    df = df.loc[:, ~df.columns.duplicated()]
    return df

# ======================
# Session State
# ======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# ======================
# Simple Login
# ======================
st.sidebar.header("🔐 Login")

if not st.session_state.logged_in:
    with st.sidebar.form("login_form"):
        email = st.text_input("Email address", placeholder="you@example.com")
        login_btn = st.form_submit_button("Login", use_container_width=True, type="primary")

        if login_btn:
            email = email.strip().lower()
            if not email:
                st.error("Please enter your email.")
            elif not is_valid_email(email):
                st.error("Please enter a valid email address.")
            else:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.success("Login successful!")
                st.rerun()
else:
    st.sidebar.success(f"Logged in as:\n**{st.session_state.user_email}**")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.session_state.pop("expenses", None)
        st.session_state.pop("income", None)
        st.rerun()

if not st.session_state.logged_in:
    st.title("💰 Expense Tracker")
    st.info("👈 Please login with your email in the sidebar to continue.")
    st.stop()

# ======================
# User Data Setup
# ======================
USER = st.session_state.user_email
safe_user = sanitize_email(USER)
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

USER_FILE = os.path.join(DATA_DIR, f"{safe_user}_expenses.csv")
INCOME_FILE = os.path.join(DATA_DIR, f"{safe_user}_income.csv")

COLUMNS = [
    "Date", "User", "Category", "Amount", "Currency",
    "Vendor", "Description", "Remark", "Source"
]

INCOME_COLUMNS = [
    "Date", "User", "Category", "Amount", "Currency",
    "Customer", "Description", "Remark", "Source"
]

CURRENCIES = ["HKD", "RMB", "JPY", "USD", "EUR"]

# ---- Expenses ----
if "expenses" not in st.session_state:
    if os.path.exists(USER_FILE):
        try:
            st.session_state.expenses = read_csv_chinese_safe(USER_FILE)
            for col in COLUMNS:
                if col not in st.session_state.expenses.columns:
                    st.session_state.expenses[col] = "HKD" if col == "Currency" else ""
            st.session_state.expenses = st.session_state.expenses[COLUMNS]
        except Exception:
            st.session_state.expenses = pd.DataFrame(columns=COLUMNS)
    else:
        st.session_state.expenses = pd.DataFrame(columns=COLUMNS)

st.session_state.expenses["Amount"] = clean_amount(st.session_state.expenses["Amount"])
st.session_state.expenses["Date"] = normalize_date_column(st.session_state.expenses["Date"])
if "Currency" in st.session_state.expenses.columns:
    st.session_state.expenses["Currency"] = st.session_state.expenses["Currency"].fillna("HKD").astype(str)
else:
    st.session_state.expenses["Currency"] = "HKD"

def save_data():
    st.session_state.expenses.to_csv(USER_FILE, index=False, encoding="utf-8-sig")

# ---- Income ----
if "income" not in st.session_state:
    if os.path.exists(INCOME_FILE):
        try:
            st.session_state.income = read_csv_chinese_safe(INCOME_FILE)
            for col in INCOME_COLUMNS:
                if col not in st.session_state.income.columns:
                    st.session_state.income[col] = "HKD" if col == "Currency" else ""
            st.session_state.income = st.session_state.income[INCOME_COLUMNS]
        except Exception:
            st.session_state.income = pd.DataFrame(columns=INCOME_COLUMNS)
    else:
        st.session_state.income = pd.DataFrame(columns=INCOME_COLUMNS)

st.session_state.income["Amount"] = clean_amount(st.session_state.income["Amount"])
st.session_state.income["Date"] = normalize_date_column(st.session_state.income["Date"])
if "Currency" in st.session_state.income.columns:
    st.session_state.income["Currency"] = st.session_state.income["Currency"].fillna("HKD").astype(str)
else:
    st.session_state.income["Currency"] = "HKD"

def save_income():
    st.session_state.income.to_csv(INCOME_FILE, index=False, encoding="utf-8-sig")

# Warn about corrupted Chinese
if (has_corrupted_chinese(st.session_state.expenses, ["Vendor", "Description", "Remark"]) or
    has_corrupted_chinese(st.session_state.income, ["Customer", "Description", "Remark"])):
    st.error(
        "⚠️ Your saved data already contains corrupted Chinese text (????).\n\n"
        "Please delete the files inside the `data` folder and re-enter the Chinese text. "
        "New entries will work correctly."
    )

# ======================
# Categories
# ======================
CATEGORIES = [
    "Food & Dining", "Transportation", "Shopping", "Bills & Utilities",
    "Entertainment", "Health", "Education", "Travel",
    "Type", "Family Support", "Health care", "Red pocket", "Assets", "Finance",
    "Property", "Transfer", "Other",
]

INCOME_CATEGORIES = [
    "Salary", "Freelance", "Business", "Investment",
    "Gift", "Refund", "Rental", "Other", "Stock"
]

SOURCES = ["Manual", "Bank", "Credit Card", "Cash", "Import", "Other"]

# ======================
# Sidebar - Add Expense
# ======================
st.sidebar.markdown("---")
st.sidebar.header("➕ Add New Expense")

with st.sidebar.form("expense_form", clear_on_submit=True):
    date = st.date_input("Date", value=datetime.now(), key="exp_date")
    category = st.selectbox("Category", CATEGORIES, key="exp_cat")
    amount = st.number_input("Amount", min_value=0.0, step=0.01, format="%.2f", key="exp_amt")
    currency = st.selectbox("Currency", CURRENCIES, index=0, key="exp_currency")
    vendor = st.text_input("Vendor", placeholder="星巴克 / Uber, 淘宝...", key="exp_vendor")
    description = st.text_input("Description", placeholder="午餐 / 月费...", key="exp_desc")
    remark = st.text_input("Remark", placeholder="可选备注...", key="exp_remark")
    source = st.selectbox("Source", SOURCES, index=0, key="exp_source")
    submitted = st.form_submit_button("Add Expense", use_container_width=True)

    if submitted:
        if amount <= 0:
            st.error("Please enter a valid amount (> 0)")
        else:
            new_row = {
                "Date": str(date),
                "User": USER,
                "Category": category,
                "Amount": float(amount),
                "Currency": currency,
                "Vendor": vendor.strip() if vendor else "-",
                "Description": description.strip() if description else "-",
                "Remark": remark.strip() if remark else "-",
                "Source": source,
            }
            st.session_state.expenses = pd.concat(
                [st.session_state.expenses, pd.DataFrame([new_row])], ignore_index=True
            )
            save_data()
            st.success(f"Added: {category} - {currency} {amount:,.2f}")
            st.rerun()

# ======================
# Sidebar - Add Income
# ======================
st.sidebar.markdown("---")
st.sidebar.header("💵 Add New Income")

with st.sidebar.form("income_form", clear_on_submit=True):
    inc_date = st.date_input("Date", value=datetime.now(), key="inc_date")
    inc_category = st.selectbox("Category", INCOME_CATEGORIES, key="inc_cat")
    inc_amount = st.number_input("Amount", min_value=0.0, step=0.01, format="%.2f", key="inc_amt")
    inc_currency = st.selectbox("Currency", CURRENCIES, index=0, key="inc_currency")
    inc_customer = st.text_input("Customer", placeholder="客户名称...", key="inc_customer")
    inc_description = st.text_input("Description", placeholder="月薪 / 项目款...", key="inc_desc")
    inc_remark = st.text_input("Remark", placeholder="可选备注...", key="inc_remark")
    inc_source = st.selectbox("Source", SOURCES, index=0, key="inc_source")
    inc_submitted = st.form_submit_button("Add Income", use_container_width=True, type="primary")

    if inc_submitted:
        if inc_amount <= 0:
            st.error("Please enter a valid amount (> 0)")
        else:
            new_inc = {
                "Date": str(inc_date),
                "User": USER,
                "Category": inc_category,
                "Amount": float(inc_amount),
                "Currency": inc_currency,
                "Customer": inc_customer.strip() if inc_customer else "-",
                "Description": inc_description.strip() if inc_description else "-",
                "Remark": inc_remark.strip() if inc_remark else "-",
                "Source": inc_source,
            }
            st.session_state.income = pd.concat(
                [st.session_state.income, pd.DataFrame([new_inc])], ignore_index=True
            )
            save_income()
            st.success(f"Income added: {inc_category} - {inc_currency} {inc_amount:,.2f}")
            st.rerun()

# ======================
# Sidebar - Upload Expenses
# ======================
st.sidebar.markdown("---")
st.sidebar.header("📥 Upload Expenses")

uploaded_file = st.sidebar.file_uploader(
    "Upload Expenses CSV",
    type=["csv"],
    help="Supports Simplified & Traditional Chinese. Prefer CSV UTF-8 from Excel.",
    key="upload_expenses",
)

if uploaded_file is not None:
    try:
        import_df = read_csv_chinese_safe(uploaded_file)
        import_df.columns = import_df.columns.astype(str).str.strip()
        original_cols = list(import_df.columns)
        import_df = normalize_columns(import_df)

        if "Currecny" in import_df.columns and "Currency" not in import_df.columns:
            import_df = import_df.rename(columns={"Currecny": "Currency"})

        min_required = {"Date", "Category", "Amount"}
        if not min_required.issubset(set(import_df.columns)):
            st.sidebar.error(
                f"Missing required columns.\nNeed at least: Date, Category, Amount\n"
                f"Found: {', '.join(original_cols)}"
            )
        else:
            defaults = {
                "User": USER, "Currency": "HKD", "Vendor": "-",
                "Description": "-", "Remark": "-", "Source": "Import"
            }
            for col, default in defaults.items():
                if col not in import_df.columns:
                    import_df[col] = default

            for col in COLUMNS:
                if col not in import_df.columns:
                    import_df[col] = defaults.get(col, "-")

            import_df = import_df[COLUMNS].copy()
            import_df["Date"] = normalize_date_column(import_df["Date"])
            import_df["Amount"] = clean_amount(import_df["Amount"])
            import_df = import_df[import_df["Amount"] > 0].copy()

            for col in ["User", "Category", "Currency", "Vendor", "Description", "Remark", "Source", "Date"]:
                import_df[col] = import_df[col].fillna(defaults.get(col, "-")).astype(str).str.strip()
                import_df.loc[import_df[col] == "", col] = defaults.get(col, "-")
                if col == "Vendor":
                    import_df.loc[import_df[col].str.lower().isin(["nan", "none", "null"]), col] = "-"

            st.sidebar.markdown(f"**Preview** ({len(import_df)} rows)")
            st.sidebar.dataframe(
                import_df[["Date", "Category", "Amount", "Currency", "Vendor"]].head(8),
                use_container_width=True, hide_index=True
            )

            if st.sidebar.button("Import Expenses", use_container_width=True, type="primary", key="import_exp"):
                before = len(st.session_state.expenses)
                st.session_state.expenses = pd.concat(
                    [st.session_state.expenses, import_df], ignore_index=True
                )
                st.session_state.expenses["Amount"] = clean_amount(st.session_state.expenses["Amount"])
                st.session_state.expenses["Date"] = normalize_date_column(st.session_state.expenses["Date"])
                save_data()
                st.sidebar.success(f"✅ Imported {len(st.session_state.expenses) - before} expenses!")
                st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error reading 
