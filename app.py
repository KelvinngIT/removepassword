import streamlit as st
from pathlib import Path
import database as db
from unlocker import ExcelUnlocker
import smtplib
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
st.write(st.secrets.get("email", "NO EMAIL SECTION FOUND"))

# Initialize database
db.init_db()

st.set_page_config(
    page_title="Excel Unlocker",
    page_icon="🔓",
    layout="centered"
)

# ---------- Session state ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "password_sent" not in st.session_state:
    st.session_state.password_sent = False
if "pending_email" not in st.session_state:
    st.session_state.pending_email = ""


# ---------- Email helper ----------
def generate_temp_password(length: int = 10) -> str:
    """Generate a secure temporary password."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def send_login_password(to_email: str, temp_password: str) -> bool:
    """
    Send the temporary password to the user's email.
    Requires secrets in .streamlit/secrets.toml:

    [email]
    sender = "your_email@gmail.com"
    password = "your_app_password"   # Gmail App Password recommended
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    """
    try:
        sender = st.secrets["email"]["sender"]
        password = st.secrets["email"]["password"]
        smtp_server = st.secrets["email"].get("smtp_server", "smtp.gmail.com")
        smtp_port = st.secrets["email"].get("smtp_port", 587)

        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = to_email
        msg["Subject"] = "Your Excel Unlocker Login Password"

        body = f"""
Hello,

You requested a login password for Excel Unlocker.

Your temporary password is:

    {temp_password}

This password is valid for a single login session.
If you did not request this, you can safely ignore this email.

Best regards,
Excel Unlocker
"""
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)

        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False


# ---------- Login / Register pages ----------
def login_page():
    st.title("🔓 Excel Unlocker")
    st.subheader("Login with Email")

    tab1, tab2 = st.tabs(["Login", "Register"])

    # ===== LOGIN TAB =====
    with tab1:
        st.markdown("Enter your email and we will send a temporary password to your inbox.")

        with st.form("request_password_form"):
            email = st.text_input("Email", key="login_email")
            send_btn = st.form_submit_button("Send Password to Email", use_container_width=True)

            if send_btn:
                email = email.strip().lower()
                if not email or "@" not in email:
                    st.error("Please enter a valid email address.")
                else:
                    # Check if user exists
                    if not db.user_exists(email):          # ← you need this helper in database.py
                        st.error("No account found with this email. Please register first.")
                    else:
                        temp_password = generate_temp_password()
                        # Save the temporary password (hashed) in the database
                        if db.set_temp_password(email, temp_password):   # ← you need this helper
                            if send_login_password(email, temp_password):
                                st.session_state.password_sent = True
                                st.session_state.pending_email = email
                                st.success("Temporary password sent! Check your email (and spam folder).")
                            else:
                                st.error("Could not send the email. Please try again later.")
                        else:
                            st.error("Failed to generate password. Please try again.")

        # Show password entry form only after a password was successfully sent
        if st.session_state.password_sent:
            st.divider()
            st.info(f"Password sent to **{st.session_state.pending_email}**. Enter it below.")

            with st.form("login_with_temp_form"):
                password = st.text_input("Temporary Password", type="password")
                login_btn = st.form_submit_button("Login", use_container_width=True)

                if login_btn:
                    if db.verify_user(st.session_state.pending_email, password):
                        st.session_state.logged_in = True
                        st.session_state.user_email = st.session_state.pending_email
                        # Clear temporary state
                        st.session_state.password_sent = False
                        st.session_state.pending_email = ""
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid or expired temporary password.")

    # ===== REGISTER TAB =====
    with tab2:
        st.markdown("Create an account. A password will be emailed to you.")

        with st.form("register_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email", key="reg_email")
            submit = st.form_submit_button("Create Account", use_container_width=True)

            if submit:
                email = email.strip().lower()
                if not name or not email or "@" not in email:
                    st.error("Please fill in all fields with a valid email.")
                else:
                    temp_password = generate_temp_password()
                    if db.create_user(email, temp_password, name):
                        if send_login_password(email, temp_password):
                            st.success(
                                "Account created! A temporary password has been sent to your email. "
                                "Please check your inbox and log in."
                            )
                        else:
                            st.warning(
                                "Account created, but we could not send the email. "
                                "Please use the Login tab and request a new password."
                            )
                    else:
                        st.error("Email already registered.")


# ---------- Main App ----------
def main_app():
    st.title("🔓 Excel Unlocker")
    st.write(f"Welcome, **{st.session_state.user_email}**")

    if st.button("Logout", type="secondary"):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.password_sent = False
        st.session_state.pending_email = ""
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
