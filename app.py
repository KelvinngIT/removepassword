import streamlit as st
from pathlib import Path
import database as db
from unlocker import ExcelUnlocker

# Initialize database
db.init_db()

st.set_page_config(
    page_title="Excel Unlocker",
    page_icon="🔓",
    layout="centered"
)

# Session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

def login_page():
    st.title("🔓 Excel Unlocker")
    st.subheader("Login to continue")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                if db.verify_user(email, password):
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid email or password")

    with tab2:
        with st.form("register_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("Password", type="password", key="reg_pass")
            confirm = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Create Account", use_container_width=True)

            if submit:
                if password != confirm:
                    st.error("Passwords do not match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    if db.create_user(email, password, name):
                        st.success("Account created! Please login.")
                    else:
                        st.error("Email already registered")

def main_app():
    st.title("🔓 Excel Unlocker")
    st.write(f"Welcome, **{st.session_state.user_email}**")

    if st.button("Logout", type="secondary"):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.rerun()

    st.divider()

    st.subheader("Upload Protected Excel File")
    uploaded_file = st.file_uploader(
        "Choose a .xlsx or .xlsm file",
        type=["xlsx", "xlsm"]
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        remove_workbook = st.checkbox("Remove Workbook Protection", value=True)
    with col2:
        remove_worksheet = st.checkbox("Remove Sheet Protection", value=True)
    with col3:
        remove_vba = st.checkbox("Remove VBA Protection", value=False)

    if uploaded_file is not None:
        # Save uploaded file temporarily
        temp_input = Path("temp_uploads")
        temp_input.mkdir(exist_ok=True)
        input_path = temp_input / uploaded_file.name

        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        if st.button("🚀 Unlock File", type="primary", use_container_width=True):
            with st.spinner("Unlocking file..."):
                try:
                    unlocker = ExcelUnlocker(str(input_path))
                    output_path = unlocker.unlock(
                        remove_workbook=remove_workbook,
                        remove_worksheet=remove_worksheet,
                        remove_vba=remove_vba
                    )

                    st.success("File unlocked successfully!")

                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download Unlocked File",
                            data=f,
                            file_name=Path(output_path).name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ====================== Run App ======================
if st.session_state.logged_in:
    main_app()
else:
    login_page()
