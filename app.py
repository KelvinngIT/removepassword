import streamlit as st
from pathlib import Path
from unlocker import ExcelUnlocker

st.set_page_config(
    page_title="Excel Unlocker",
    page_icon="🔓",
    layout="centered"
)

# ======================
# Session State
# ======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# ======================
# Support the Writer
# ======================
def support_writer():
    st.markdown("---")
    st.markdown(
        """
        <div style="
            background-color: #f8f9fa;
            border-radius: 12px;
            padding: 20px 24px;
            text-align: center;
            margin-top: 30px;
            border: 1px solid #e9ecef;
        ">
            <div style="font-size: 1.25rem; font-weight: 600; margin-bottom: 8px;">
                ❤️ Support the Writer
            </div>
            <p style="color: #555; margin-bottom: 18px; font-size: 0.95rem;">
                If this tool helped you, consider buying me a coffee!
            </p>
            <a href="https://www.buymeacoffee.com/yourusername" target="_blank" style="text-decoration: none;">
                <div style="
                    display: inline-flex;
                    align-items: center;
                    gap: 10px;
                    background-color: #FFDD00;
                    color: #000000;
                    font-weight: 700;
                    font-size: 1.1rem;
                    padding: 12px 28px;
                    border-radius: 50px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    transition: all 0.2s ease;
                ">
                    <span style="font-size: 1.4rem;">☕</span>
                    Buy me a coffee
                </div>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

# ======================
# Simple Email Login
# ======================
def login_page():
    st.title("🔓 Excel Unlocker")
    st.subheader("Login with your email")

    with st.form("login_form"):
        email = st.text_input("Email address", placeholder="you@example.com")
        submit = st.form_submit_button("Login", use_container_width=True, type="primary")

        if submit:
            email = email.strip().lower()
            if not email:
                st.error("Please enter your email.")
            elif "@" not in email or "." not in email:
                st.error("Please enter a valid email address.")
            else:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.success("Login successful!")
                st.rerun()

# ======================
# Main App
# ======================
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

    # Support section at the bottom
    support_writer()

# ======================
# Run App
# ======================
if st.session_state.logged_in:
    main_app()
else:
    login_page()
