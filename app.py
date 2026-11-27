import streamlit as st
from pathlib import Path
from unlocker import ExcelUnlocker
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_LINE_SPACING
from io import BytesIO

st.set_page_config(
    page_title="Excel Unlocker + APA Formatter",
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
# Support the Writer (Sidebar)
# ======================
def support_writer():
    st.sidebar.markdown("---")
    st.sidebar.subheader("💖 Support the Writer")
    st.sidebar.markdown("If this tool helped you, consider buying me a coffee!")
    st.sidebar.markdown(
        '''
        <a href="https://www.buymeacoffee.com/itmasterngw" target="_blank">
            <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png"
                 alt="Buy Me A Coffee"
                 style="height: 60px !important; width: 217px !important;">
        </a>
        ''',
        unsafe_allow_html=True
    )

support_writer()

# ======================
# APA Conversion Function
# ======================
def convert_to_apa_format(doc: Document) -> Document:
    """
    Convert Word document to APA format:
    - Times New Roman
    - 12 point
    - Double spacing
    - 1-inch margins
    """
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)

    paragraph_format = style.paragraph_format
    paragraph_format.line_spacing_rule = WD_LINE_SPACING.DOUBLE

    for paragraph in doc.paragraphs:
        paragraph.style = doc.styles['Normal']
        paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.DOUBLE
        for run in paragraph.runs:
            run.font.name = 'Times New Roman'
            run.font.size = Pt(12)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.DOUBLE
                    for run in paragraph.runs:
                        run.font.name = 'Times New Roman'
                        run.font.size = Pt(12)

    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    return doc

# ======================
# Login Page
# ======================
def login_page():
    st.title("🔓 Excel Unlocker + APA Formatter")
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
    st.title("🔓 Excel Unlocker + APA Formatter")
    st.write(f"Welcome, **{st.session_state.user_email}**")

    if st.button("Logout", type="secondary"):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.rerun()

    st.divider()

    # ---------- Excel Unlocker Section ----------
    st.subheader("1️⃣ Unlock Protected Excel File")
    uploaded_excel = st.file_uploader(
        "Choose a .xlsx or .xlsm file",
        type=["xlsx", "xlsm"],
        key="excel_uploader"
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        remove_workbook = st.checkbox("Remove Workbook Protection", value=True)
    with col2:
        remove_worksheet = st.checkbox("Remove Sheet Protection", value=True)
    with col3:
        remove_vba = st.checkbox("Remove VBA Protection", value=False)

    if uploaded_excel is not None:
        temp_input = Path("temp_uploads")
        temp_input.mkdir(exist_ok=True)
        input_path = temp_input / uploaded_excel.name

        with open(input_path, "wb") as f:
            f.write(uploaded_excel.getbuffer())

        if st.button("🚀 Unlock Excel File", type="primary", use_container_width=True):
            with st.spinner("Unlocking file..."):
                try:
                    unlocker = ExcelUnlocker(str(input_path))
                    output_path = unlocker.unlock(
                        remove_workbook=remove_workbook,
                        remove_worksheet=remove_worksheet,
                        remove_vba=remove_vba
                    )
                    st.success("Excel file unlocked successfully!")

                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="⬇️ Download Unlocked Excel",
                            data=f,
                            file_name=Path(output_path).name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    st.divider()

    # ---------- APA Word Formatter Section ----------
    st.subheader("2️⃣ Convert Word Document to APA Format")
    st.caption("Times New Roman • 12 pt • Double-spaced • 1-inch margins")

    uploaded_word = st.file_uploader(
        "Upload a Word file (.docx)",
        type=["docx"],
        key="word_uploader"
    )

    if uploaded_word is not None:
        if st.button("📄 Convert to APA Format", type="primary", use_container_width=True):
            with st.spinner("Converting to APA format..."):
                try:
                    doc = Document(uploaded_word)
                    apa_doc = convert_to_apa_format(doc)

                    buffer = BytesIO()
                    apa_doc.save(buffer)
                    buffer.seek(0)

                    st.success("✅ Document successfully converted to APA format!")

                    st.download_button(
                        label="⬇️ Download APA Formatted Document",
                        data=buffer,
                        file_name=f"APA_{uploaded_word.name}",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error converting file: {str(e)}")

# ======================
# Run App
# ======================
if st.session_state.logged_in:
    main_app()
else:
    login_page()
