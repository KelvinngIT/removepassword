def send_login_password(to_email: str, temp_password: str) -> bool:
    """Send the temporary password to the user's email."""
    try:
        # Check if secrets exist
        if "email" not in st.secrets:
            st.error("""
            ❌ Email secrets are not configured.
            
            Please add the following in Streamlit Cloud → Settings → Secrets:
            
            [email]
            sender = "your_email@gmail.com"
            password = "your_app_password"
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            """)
            return False

        sender = st.secrets["email"]["sender"]
        password = st.secrets["email"]["password"]
        smtp_server = st.secrets["email"].get("smtp_server", "smtp.gmail.com")
        smtp_port = int(st.secrets["email"].get("smtp_port", 587))

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
